"""Verification service: configurable templates, TAT, fraud detection, audit."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Employee,
    User,
    Verification,
    VerificationFraudFlag,
    VerificationTemplate,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Templates ────────────────────────────────────────────────────────
async def create_template(
    db: AsyncSession, *, payload: dict
) -> VerificationTemplate:
    existing = (
        await db.execute(
            select(VerificationTemplate).where(
                VerificationTemplate.code == payload["code"]
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError(f"Template '{payload['code']}' already exists")
    fields = payload.get("fields") or []
    if not fields:
        raise ValidationError("Template must have at least one field")
    photo_reqs = payload.get("photo_requirements")
    template = VerificationTemplate(
        code=payload["code"],
        name=payload["name"],
        type=payload["type"],
        description=payload.get("description"),
        fields=[
            f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in fields
        ],
        photo_requirements=(
            [
                p.model_dump() if hasattr(p, "model_dump") else dict(p)
                for p in photo_reqs
            ]
            if photo_reqs
            else None
        ),
        signature_required=payload.get("signature_required", False),
        sla_hours=payload.get("sla_hours", 48),
        is_active=True,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def list_templates(
    db: AsyncSession, *, active_only: bool = True
) -> Sequence[VerificationTemplate]:
    stmt = select(VerificationTemplate)
    if active_only:
        stmt = stmt.where(VerificationTemplate.is_active.is_(True))
    stmt = stmt.order_by(VerificationTemplate.name.asc())
    return (await db.execute(stmt)).scalars().all()


async def get_template(
    db: AsyncSession, template_id: int
) -> VerificationTemplate:
    t = (
        await db.execute(
            select(VerificationTemplate).where(
                VerificationTemplate.id == template_id
            )
        )
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Verification template not found")
    return t


# ── Verification jobs ────────────────────────────────────────────────
async def _next_ticket_number(db: AsyncSession) -> str:
    year = _now().year
    prefix = f"JKT/V/{year}/"
    last = (
        await db.execute(
            select(Verification.ticket_number)
            .where(Verification.ticket_number.like(f"{prefix}%"))
            .order_by(Verification.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    seq = 1
    if last:
        try:
            seq = int(last.split("/")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:05d}"


async def create_verification(
    db: AsyncSession, *, payload: dict
) -> Verification:
    template = await get_template(db, payload["template_id"])
    if not template.is_active:
        raise ValidationError("Template is inactive")

    if payload.get("assigned_to"):
        emp = (
            await db.execute(
                select(Employee).where(Employee.id == payload["assigned_to"])
            )
        ).scalar_one_or_none()
        if not emp:
            raise NotFoundError("Employee not found")

    now = _now()
    v = Verification(
        ticket_number=await _next_ticket_number(db),
        template_id=template.id,
        type=template.type,
        subject_name=payload["subject_name"],
        subject_data=payload["subject_data"],
        address=payload.get("address"),
        contact_phone=payload.get("contact_phone"),
        requested_by_org=payload.get("requested_by_org"),
        assigned_to=payload.get("assigned_to"),
        assigned_at=now,
        deadline_at=now + timedelta(hours=template.sla_hours),
        status="pending",
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)

    # Trigger automatic fraud detection (duplicate subject)
    await _detect_duplicate_subject(db, v)
    return v


async def _detect_duplicate_subject(
    db: AsyncSession, verification: Verification
) -> None:
    """Flag verifications for the same subject within the last 30 days."""
    since = _now() - timedelta(days=30)
    rows = (
        await db.execute(
            select(Verification)
            .where(Verification.id != verification.id)
            .where(Verification.subject_name == verification.subject_name)
            .where(Verification.type == verification.type)
            .where(Verification.created_at >= since)
        )
    ).scalars().all()
    if rows:
        flag = VerificationFraudFlag(
            verification_id=verification.id,
            flag_type="duplicate_subject",
            severity="medium",
            detected_by="system",
            notes=f"Subject was verified {len(rows)} time(s) in the last 30 days",
            detected_at=_now(),
        )
        db.add(flag)
        await db.commit()


async def list_verifications(
    db: AsyncSession,
    *,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    type_: Optional[str] = None,
    limit: int = 200,
) -> Sequence[Verification]:
    stmt = select(Verification)
    if assigned_to is not None:
        stmt = stmt.where(Verification.assigned_to == assigned_to)
    if status:
        stmt = stmt.where(Verification.status == status)
    if type_:
        stmt = stmt.where(Verification.type == type_)
    stmt = stmt.order_by(Verification.created_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


async def get_verification(db: AsyncSession, vid: int) -> Verification:
    v = (
        await db.execute(select(Verification).where(Verification.id == vid))
    ).scalar_one_or_none()
    if not v:
        raise NotFoundError("Verification not found")
    return v


async def start_verification(
    db: AsyncSession, vid: int, *, employee: Employee
) -> Verification:
    v = await get_verification(db, vid)
    if v.assigned_to != employee.id:
        raise ForbiddenError("Not your verification")
    if v.status not in ("pending", "in_progress"):
        raise ValidationError(f"Cannot start a {v.status} verification")
    v.status = "in_progress"
    await db.commit()
    await db.refresh(v)
    return v


def _validate_form_against_template(
    template: VerificationTemplate, form_data: dict, photos: list | None
) -> None:
    field_specs = template.fields or []
    missing = []
    for spec in field_specs:
        if spec.get("required") and not form_data.get(spec["key"]):
            missing.append(spec["key"])
    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )
    photo_reqs = template.photo_requirements or []
    required_photos = [p["key"] for p in photo_reqs if p.get("required")]
    if required_photos and not photos:
        raise ValidationError(
            f"Missing required photos: {', '.join(required_photos)}"
        )


async def submit_verification(
    db: AsyncSession,
    vid: int,
    *,
    employee: Employee,
    payload: dict,
) -> Verification:
    v = await get_verification(db, vid)
    if v.assigned_to != employee.id:
        raise ForbiddenError("Not your verification")
    if v.status not in ("pending", "in_progress"):
        raise ValidationError(f"Cannot submit a {v.status} verification")

    template = await get_template(db, v.template_id)
    _validate_form_against_template(
        template, payload["form_data"], payload.get("photos")
    )
    if template.signature_required and not payload.get("signature_url"):
        raise ValidationError("Signature is required for this template")

    v.form_data = payload["form_data"]
    v.photos = payload.get("photos")
    v.signature_url = payload.get("signature_url")
    if payload.get("geo_lat") is not None:
        v.geo_lat = str(payload["geo_lat"])
    if payload.get("geo_lng") is not None:
        v.geo_lng = str(payload["geo_lng"])
    v.result = payload["result"]
    v.remarks = payload.get("remarks")
    v.submitted_at = _now()
    v.status = "audit_pending"
    await db.commit()

    # Heuristic fraud check: form submitted with negative result but no remarks.
    if v.result == "negative" and not v.remarks:
        db.add(
            VerificationFraudFlag(
                verification_id=v.id,
                flag_type="form_inconsistent",
                severity="low",
                detected_by="system",
                notes="Negative result without remarks",
                detected_at=_now(),
            )
        )
        await db.commit()

    await db.refresh(v)
    return v


async def audit_verification(
    db: AsyncSession,
    vid: int,
    *,
    auditor: User,
    audit_status: str,
    audit_comments: Optional[str] = None,
) -> Verification:
    v = await get_verification(db, vid)
    if v.status != "audit_pending":
        raise ValidationError("Only audit-pending verifications can be audited")
    v.audited_by = auditor.id
    v.audited_at = _now()
    v.audit_status = audit_status
    v.audit_comments = audit_comments
    if audit_status == "approved":
        v.status = "audit_passed"
        # Mark completed once approved
        v.status = "completed"
    elif audit_status == "rejected":
        v.status = "audit_failed"
        # Add suspicious pattern flag
        db.add(
            VerificationFraudFlag(
                verification_id=v.id,
                flag_type="suspicious_pattern",
                severity="high",
                detected_by="auditor",
                notes=audit_comments or "Auditor rejected the submission",
                detected_at=_now(),
            )
        )
    elif audit_status == "rework":
        # Send back to the field employee
        v.status = "in_progress"
        v.submitted_at = None
    await db.commit()
    await db.refresh(v)
    return v


async def add_fraud_flag(
    db: AsyncSession,
    vid: int,
    *,
    auditor: User,
    flag_type: str,
    severity: str = "medium",
    notes: Optional[str] = None,
) -> VerificationFraudFlag:
    v = await get_verification(db, vid)
    flag = VerificationFraudFlag(
        verification_id=v.id,
        flag_type=flag_type,
        severity=severity,
        detected_by="auditor",
        notes=notes,
        detected_at=_now(),
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return flag


async def tat_stats(
    db: AsyncSession,
    *,
    assigned_to: Optional[int] = None,
) -> dict:
    """Compute TAT/SLA stats for completed verifications."""
    stmt = select(Verification).where(Verification.status == "completed")
    if assigned_to is not None:
        stmt = stmt.where(Verification.assigned_to == assigned_to)
    rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        return {
            "total": 0,
            "on_time": 0,
            "breached": 0,
            "avg_hours": 0.0,
            "breach_pct": 0.0,
        }
    total = len(rows)
    on_time = 0
    breached = 0
    durations = []
    for v in rows:
        end = v.audited_at or v.submitted_at
        if end:
            hours = (end - v.assigned_at).total_seconds() / 3600
            durations.append(hours)
            if v.deadline_at and end <= v.deadline_at:
                on_time += 1
            else:
                breached += 1
    avg = sum(durations) / len(durations) if durations else 0.0
    return {
        "total": total,
        "on_time": on_time,
        "breached": breached,
        "avg_hours": round(avg, 2),
        "breach_pct": round((breached / total) * 100, 2) if total else 0.0,
    }

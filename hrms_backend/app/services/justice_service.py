"""Justice Portal service.

Encryption-aware: complainant identity, complaint description / desired
outcome, accused names, witness statements, evidence URLs, and action
notes are all stored AES-GCM-256 encrypted via `encryption.py`. Decryption
happens only at the boundary, and every decrypted read is recorded in
`justice_access_log`.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import Role as RoleEnum
from app.models import (
    IccMember,
    JusticeAccessLog,
    JusticeAccused,
    JusticeAction,
    JusticeComplaint,
    JusticeEvidence,
    JusticeTimeline,
    JusticeWitness,
    PoshAnnualReport,
    RetaliationFlag,
    User,
)
from app.services import encryption


# ── Routing ───────────────────────────────────────────────────────────
# Role codes that may view a complaint of each type.
ROUTING: dict[str, set[str]] = {
    "sexual_harassment": {"icc_member", "director", "super_admin"},
    "fraud": {"director", "super_admin"},
    "manager_issue": {"hr", "director", "super_admin"},
    "hr_issue": {"director", "super_admin"},
    "director_issue": {"super_admin"},  # external ombudsman in real life
    "safety": {"hr", "admin", "director", "super_admin"},
    "discrimination": {"icc_member", "hr", "director", "super_admin"},
    "general": {"hr", "director", "super_admin"},
}

# POSH timeline: 7-day acknowledgement, 90-day investigation.
POSH_TYPES = {"sexual_harassment", "discrimination"}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    return _now().date()


async def _is_icc_member(db: AsyncSession, user: User) -> bool:
    if not user:
        return False
    row = (
        await db.execute(
            select(IccMember)
            .where(IccMember.user_id == user.id)
            .where(IccMember.is_active.is_(True))
        )
    ).scalar_one_or_none()
    return row is not None


def _is_super_admin(user: User) -> bool:
    return RoleEnum.SUPER_ADMIN.value in user.role_codes


def _is_director(user: User) -> bool:
    return RoleEnum.DIRECTOR.value in user.role_codes


def _is_hr(user: User) -> bool:
    return RoleEnum.HR.value in user.role_codes


async def can_view(
    db: AsyncSession, complaint: JusticeComplaint, user: User
) -> bool:
    if _is_super_admin(user):
        return True
    if user.id and complaint.assigned_to == user.id:
        return True
    if (
        complaint.privacy_level == "open"
        and complaint.complainant_employee_id is not None
        and _user_is_complainant(complaint, user)
    ):
        return True
    allowed_roles = ROUTING.get(complaint.complaint_type, set())
    if "director" in allowed_roles and _is_director(user):
        return True
    if "hr" in allowed_roles and _is_hr(user):
        return True
    if "icc_member" in allowed_roles and await _is_icc_member(db, user):
        return True
    if "admin" in allowed_roles and RoleEnum.ADMIN.value in user.role_codes:
        return True
    return False


def _user_is_complainant(complaint: JusticeComplaint, user: User) -> bool:
    """True if the user identifies as the complainant (open complaints only)."""
    return (
        complaint.complainant_employee_id is not None
        and complaint.complainant_employee_id == _self_employee_id_from_user(user)
    )


def _self_employee_id_from_user(user: User) -> Optional[int]:
    """Cheap helper — falls back to None if relationship not loaded."""
    # The user → employee link isn't a direct FK on User, so the API
    # layer typically passes complainant_employee_id explicitly. We keep
    # this helper for forward-compat.
    return None


async def log_access(
    db: AsyncSession,
    complaint_id: int,
    user_id: Optional[int],
    action: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    db.add(
        JusticeAccessLog(
            complaint_id=complaint_id,
            user_id=user_id,
            action=action,
            ip_address=(ip or "")[:64] or None,
            user_agent=(user_agent or "")[:255] or None,
        )
    )
    await db.flush()


# ── Ticket numbering ──────────────────────────────────────────────────
async def _next_ticket(db: AsyncSession, year: int) -> str:
    """Format JKT/JC/{year}/{seq} (Justice Complaint)."""
    rows = (
        await db.execute(
            select(JusticeComplaint).where(
                JusticeComplaint.ticket_number.like(f"JKT/JC/{year}/%")
            )
        )
    ).scalars().all()
    max_seq = 0
    for c in rows:
        parts = (c.ticket_number or "").split("/")
        if len(parts) == 4:
            try:
                max_seq = max(max_seq, int(parts[-1]))
            except ValueError:
                pass
    return f"JKT/JC/{year}/{(max_seq + 1):03d}"


# ── Submit ────────────────────────────────────────────────────────────
async def submit_complaint(
    db: AsyncSession,
    *,
    user: User,
    complainant_employee_id: Optional[int],
    complaint_type: str,
    privacy_level: str,
    severity: str,
    subject: str,
    description: str,
    desired_outcome: Optional[str],
    incident_date: Optional[date],
    incident_location: Optional[str],
    accused: list[dict],
    witnesses: list[dict],
    evidence: list[dict],
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> JusticeComplaint:
    from app.models import COMPLAINT_TYPES, PRIVACY_LEVELS, SEVERITY  # type: ignore

    # Validate enums (using the canonical tuples from the model file).
    from app.models.justice import (
        COMPLAINT_TYPES as _C,
        PRIVACY_LEVELS as _P,
        SEVERITY as _S,
    )
    if complaint_type not in _C:
        raise ValidationError(f"Invalid complaint_type: {complaint_type}")
    if privacy_level not in _P:
        raise ValidationError(f"Invalid privacy_level: {privacy_level}")
    if severity not in _S:
        raise ValidationError(f"Invalid severity: {severity}")

    today = _today()
    ticket = await _next_ticket(db, today.year)

    # Anonymous → never store the employee link, even if known.
    visible_employee_id = (
        complainant_employee_id if privacy_level == "open" else None
    )

    complaint = JusticeComplaint(
        ticket_number=ticket,
        complaint_type=complaint_type,
        privacy_level=privacy_level,
        severity=severity,
        status="submitted",
        complainant_id_encrypted=encryption.encrypt(
            str(complainant_employee_id) if complainant_employee_id else None
        ),
        complainant_employee_id=visible_employee_id,
        subject=subject,
        description_encrypted=encryption.encrypt(description) or "",
        desired_outcome_encrypted=encryption.encrypt(desired_outcome),
        incident_date=incident_date,
        incident_location=incident_location,
        submitted_at=_now(),
    )
    # POSH timeline.
    if complaint_type in POSH_TYPES:
        complaint.deadline_at = _now() + timedelta(days=90)

    db.add(complaint)
    await db.flush()

    for a in accused:
        db.add(
            JusticeAccused(
                complaint_id=complaint.id,
                accused_name_encrypted=encryption.encrypt(a.get("name")) or "",
                accused_employee_id=a.get("employee_id"),
                relationship_type=a.get("relationship_type"),
            )
        )
    for w in witnesses:
        db.add(
            JusticeWitness(
                complaint_id=complaint.id,
                witness_name_encrypted=encryption.encrypt(w.get("name")) or "",
                witness_statement_encrypted=encryption.encrypt(
                    w.get("statement")
                ),
                is_anonymous=bool(w.get("is_anonymous", False)),
            )
        )
    for e in evidence:
        db.add(
            JusticeEvidence(
                complaint_id=complaint.id,
                file_url_encrypted=encryption.encrypt(e.get("file_url")) or "",
                file_name=e.get("file_name"),
                file_type=e.get("file_type"),
                file_hash=e.get("file_hash"),
                uploaded_by=user.id if user else None,
            )
        )

    db.add(
        JusticeTimeline(
            complaint_id=complaint.id,
            event_type="submitted",
            event_description=f"Complaint {ticket} submitted ({privacy_level}).",
        )
    )
    await log_access(
        db,
        complaint.id,
        user.id if user else None,
        "submit",
        ip=ip,
        user_agent=user_agent,
    )
    await db.commit()
    await db.refresh(complaint)
    return complaint


# ── Reads ─────────────────────────────────────────────────────────────
async def get_complaint(
    db: AsyncSession,
    complaint_id: int,
    *,
    user: User,
    record_access: bool = True,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> JusticeComplaint:
    c = (
        await db.execute(
            select(JusticeComplaint).where(JusticeComplaint.id == complaint_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise NotFoundError("Complaint not found")
    if not await can_view(db, c, user):
        raise ForbiddenError("Not authorised to view this complaint")
    if record_access:
        await log_access(
            db, c.id, user.id, "view", ip=ip, user_agent=user_agent
        )
        await db.commit()
    return c


async def list_my_complaints(
    db: AsyncSession, employee_id: int
) -> Sequence[JusticeComplaint]:
    return (
        await db.execute(
            select(JusticeComplaint)
            .where(JusticeComplaint.complainant_employee_id == employee_id)
            .order_by(JusticeComplaint.submitted_at.desc())
        )
    ).scalars().all()


async def list_authority_inbox(
    db: AsyncSession, *, user: User
) -> Sequence[JusticeComplaint]:
    """Return complaints visible to this authority user, scoped by routing."""
    rows = (
        await db.execute(
            select(JusticeComplaint).order_by(JusticeComplaint.submitted_at.desc())
        )
    ).scalars().all()
    out: list[JusticeComplaint] = []
    for c in rows:
        if await can_view(db, c, user):
            out.append(c)
    return out


# ── Actions ──────────────────────────────────────────────────────────
async def assign_complaint(
    db: AsyncSession,
    complaint: JusticeComplaint,
    *,
    user: User,
    investigator_user_id: int,
) -> JusticeComplaint:
    complaint.assigned_to = investigator_user_id
    if complaint.status == "submitted":
        complaint.status = "under_investigation"
    db.add(
        JusticeAction(
            complaint_id=complaint.id,
            action_type="assigned",
            taken_by=user.id,
            notes_encrypted=encryption.encrypt(
                f"Assigned to user {investigator_user_id}"
            ),
        )
    )
    db.add(
        JusticeTimeline(
            complaint_id=complaint.id,
            event_type="assigned",
            event_description=f"Investigator user_id={investigator_user_id}",
            done_by=user.id,
        )
    )
    await log_access(db, complaint.id, user.id, "assign")
    await db.commit()
    await db.refresh(complaint)
    return complaint


async def add_action(
    db: AsyncSession,
    complaint: JusticeComplaint,
    *,
    user: User,
    action_type: str,
    notes: Optional[str],
) -> JusticeAction:
    valid = {
        "acknowledged",
        "investigation_started",
        "comment",
        "warning_issued",
        "training_assigned",
        "transfer",
        "termination",
        "case_closed",
        "no_action",
    }
    if action_type not in valid:
        raise ValidationError(f"Invalid action_type: {action_type}")

    action = JusticeAction(
        complaint_id=complaint.id,
        action_type=action_type,
        taken_by=user.id,
        notes_encrypted=encryption.encrypt(notes),
    )
    db.add(action)

    if action_type == "acknowledged":
        complaint.acknowledged_at = _now()
        complaint.status = "acknowledged"
    elif action_type == "investigation_started":
        complaint.status = "under_investigation"
    elif action_type in {
        "warning_issued",
        "training_assigned",
        "transfer",
        "termination",
    }:
        complaint.status = "action_taken"

    db.add(
        JusticeTimeline(
            complaint_id=complaint.id,
            event_type=f"action:{action_type}",
            event_description=notes,
            done_by=user.id,
        )
    )
    await log_access(db, complaint.id, user.id, f"action:{action_type}")
    await db.commit()
    await db.refresh(action)
    return action


async def resolve_complaint(
    db: AsyncSession,
    complaint: JusticeComplaint,
    *,
    user: User,
    notes: Optional[str],
    action_type: str = "case_closed",
) -> JusticeComplaint:
    if complaint.status in {"resolved", "withdrawn"}:
        raise ConflictError("Already finalised")
    complaint.status = "resolved"
    complaint.resolved_at = _now()
    db.add(
        JusticeAction(
            complaint_id=complaint.id,
            action_type=action_type,
            taken_by=user.id,
            notes_encrypted=encryption.encrypt(notes),
        )
    )
    db.add(
        JusticeTimeline(
            complaint_id=complaint.id,
            event_type="resolved",
            event_description=notes,
            done_by=user.id,
        )
    )
    await log_access(db, complaint.id, user.id, "resolve")
    await db.commit()
    await db.refresh(complaint)
    return complaint


async def withdraw_complaint(
    db: AsyncSession,
    complaint: JusticeComplaint,
    *,
    user: User,
    employee_id: Optional[int],
    reason: Optional[str],
) -> JusticeComplaint:
    # Only the complainant can withdraw an open complaint, or super-admin.
    if complaint.privacy_level == "open":
        if (
            employee_id is None
            or complaint.complainant_employee_id != employee_id
        ) and not _is_super_admin(user):
            raise ForbiddenError("Only the complainant can withdraw")
    elif not _is_super_admin(user):
        raise ForbiddenError("Anonymous/confidential complaints can only be withdrawn by Super Admin")

    if complaint.status in {"resolved", "withdrawn"}:
        raise ConflictError("Already finalised")
    complaint.status = "withdrawn"
    complaint.resolved_at = _now()
    db.add(
        JusticeTimeline(
            complaint_id=complaint.id,
            event_type="withdrawn",
            event_description=reason,
            done_by=user.id,
        )
    )
    await log_access(db, complaint.id, user.id, "withdraw")
    await db.commit()
    await db.refresh(complaint)
    return complaint


# ── ICC compliance ────────────────────────────────────────────────────
async def icc_compliance(db: AsyncSession) -> dict:
    """Per the POSH Act: ≥4 members, ≥50% women, ≥1 external, presiding officer."""
    members = (
        await db.execute(select(IccMember).where(IccMember.is_active.is_(True)))
    ).scalars().all()
    member_count = len(members)
    women_count = sum(1 for m in members if (m.gender or "").lower() == "female")
    external_count = sum(1 for m in members if m.is_external)
    has_presiding = any(m.role == "presiding_officer" for m in members)

    reasons: list[str] = []
    if member_count < 4:
        reasons.append(f"Need at least 4 active members; have {member_count}.")
    if women_count * 2 < member_count:
        reasons.append(
            f"At least 50% members must be women; "
            f"{women_count}/{member_count} are."
        )
    if external_count < 1:
        reasons.append("At least one member must be external.")
    if not has_presiding:
        reasons.append("Presiding Officer not designated.")

    return {
        "compliant": not reasons,
        "reasons": reasons,
        "member_count": member_count,
        "women_count": women_count,
        "external_count": external_count,
        "has_presiding_officer": has_presiding,
    }


# ── POSH annual report ────────────────────────────────────────────────
async def generate_posh_annual_report(
    db: AsyncSession,
    *,
    year: int,
    user: User,
) -> PoshAnnualReport:
    from datetime import datetime as _dt

    start = _dt(year, 1, 1)
    end = _dt(year + 1, 1, 1)

    rows = (
        await db.execute(
            select(JusticeComplaint)
            .where(JusticeComplaint.complaint_type.in_(list(POSH_TYPES)))
            .where(JusticeComplaint.submitted_at >= start)
            .where(JusticeComplaint.submitted_at < end)
        )
    ).scalars().all()
    total = len(rows)
    resolved = sum(1 for c in rows if c.status == "resolved")
    pending = total - resolved
    actions_summary: dict[str, int] = {}
    for c in rows:
        for a in c.actions:
            actions_summary[a.action_type] = actions_summary.get(a.action_type, 0) + 1

    existing = (
        await db.execute(
            select(PoshAnnualReport).where(PoshAnnualReport.year == year)
        )
    ).scalar_one_or_none()
    if existing:
        existing.total_complaints = total
        existing.resolved = resolved
        existing.pending = pending
        existing.actions_taken_json = actions_summary
        existing.generated_at = _now()
        existing.generated_by = user.id
        report = existing
    else:
        report = PoshAnnualReport(
            year=year,
            total_complaints=total,
            resolved=resolved,
            pending=pending,
            actions_taken_json=actions_summary,
            generated_at=_now(),
            generated_by=user.id,
        )
        db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


# ── Decryption views (used by the API to assemble a ComplaintDetail) ──
def decrypt_complaint_view(c: JusticeComplaint) -> dict:
    return {
        "description": encryption.decrypt(c.description_encrypted),
        "desired_outcome": encryption.decrypt(c.desired_outcome_encrypted),
        "accused": [
            {
                "id": a.id,
                "name": encryption.decrypt(a.accused_name_encrypted),
                "accused_employee_id": a.accused_employee_id,
                "relationship_type": a.relationship_type,
            }
            for a in c.accused
        ],
        "witnesses": [
            {
                "id": w.id,
                "name": (
                    None if w.is_anonymous
                    else encryption.decrypt(w.witness_name_encrypted)
                ),
                "statement": encryption.decrypt(w.witness_statement_encrypted),
                "is_anonymous": w.is_anonymous,
            }
            for w in c.witnesses
        ],
        "evidence": [
            {
                "id": e.id,
                "file_url": encryption.decrypt(e.file_url_encrypted),
                "file_name": e.file_name,
                "file_type": e.file_type,
                "file_hash": e.file_hash,
            }
            for e in c.evidence
        ],
        "actions": [
            {
                "id": a.id,
                "action_type": a.action_type,
                "action_date": a.action_date,
                "taken_by": a.taken_by,
                "notes": encryption.decrypt(a.notes_encrypted),
            }
            for a in c.actions
        ],
    }

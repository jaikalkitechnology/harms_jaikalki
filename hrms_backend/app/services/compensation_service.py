"""Salary revision workflow.

State machine:
  draft → pending_approval → approved → applied
                          ↘ rejected
                          ↘ cancelled (by proposer)
"""
from __future__ import annotations

import io
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Designation,
    Employee,
    SalaryRevision,
    SalaryTemplate,
    User,
)
from app.services.salary_calculator import JaikalkiSalaryCalculator


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _two(value: Decimal | int | float) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _three(value: Decimal | int | float) -> Decimal:
    return Decimal(value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


# ── Drafting ────────────────────────────────────────────────────────
async def propose(
    db: AsyncSession,
    *,
    proposer: User,
    employee_id: int,
    new_ctc_annual: Decimal | int | float,
    effective_date: date,
    reason: str,
    new_template_id: Optional[int] = None,
    new_designation_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> SalaryRevision:
    emp = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")
    if emp.status != "active":
        raise ValidationError("Cannot revise a non-active employee")

    open_existing = (
        await db.execute(
            select(SalaryRevision)
            .where(SalaryRevision.employee_id == employee_id)
            .where(
                SalaryRevision.status.in_(
                    ["draft", "pending_approval", "approved"]
                )
            )
        )
    ).scalar_one_or_none()
    if open_existing:
        raise ConflictError(
            "An open salary revision already exists for this employee"
        )

    new_ctc = _two(new_ctc_annual)
    prev_ctc = _two(emp.ctc_annual or 0)
    if new_ctc <= 0:
        raise ValidationError("new_ctc_annual must be positive")
    if effective_date < date.today():
        raise ValidationError("effective_date must be today or later")
    increment_pct = _three(
        (new_ctc - prev_ctc) / prev_ctc * 100 if prev_ctc > 0 else 0
    )

    # Compute the new breakup snapshot using the (resolved) template.
    template_id = new_template_id or emp.salary_template_id
    breakup_snapshot = None
    if template_id:
        template = (
            await db.execute(
                select(SalaryTemplate).where(SalaryTemplate.id == template_id)
            )
        ).scalar_one_or_none()
        if template:
            breakup = JaikalkiSalaryCalculator().calculate(template, new_ctc)
            breakup_snapshot = {
                "monthly": {
                    "basic": breakup.basic,
                    "hra": breakup.hra,
                    "other_allowance": breakup.other_allowance,
                    "conveyance": breakup.conveyance,
                    "gross": breakup.gross_monthly,
                    "pf_employee": breakup.pf_employee,
                    "esic_employee": breakup.esic_employee,
                    "professional_tax": breakup.professional_tax,
                    "net": breakup.net_monthly,
                },
                "annual": {
                    "ctc": int(new_ctc),
                    "gross": breakup.gross_annual,
                    "net": breakup.net_annual,
                },
            }

    rev = SalaryRevision(
        employee_id=emp.id,
        proposed_by=proposer.id,
        reason=reason,
        previous_ctc_annual=prev_ctc,
        new_ctc_annual=new_ctc,
        increment_pct=increment_pct,
        new_salary_template_id=new_template_id,
        new_designation_id=new_designation_id,
        effective_date=effective_date,
        notes=notes,
        breakup_snapshot=breakup_snapshot,
        status="pending_approval",
    )
    db.add(rev)
    await db.commit()
    await db.refresh(rev)
    return rev


async def approve(
    db: AsyncSession, revision_id: int, *, approver: User
) -> SalaryRevision:
    rev = await get(db, revision_id)
    if rev.status != "pending_approval":
        raise ValidationError(f"Cannot approve a revision in {rev.status!r}")
    if rev.proposed_by == approver.id:
        raise ForbiddenError(
            "An approver cannot also be the proposer of the revision"
        )
    rev.status = "approved"
    rev.approved_by = approver.id
    rev.approved_at = _now()
    await db.commit()
    await db.refresh(rev)
    return rev


async def reject(
    db: AsyncSession,
    revision_id: int,
    *,
    approver: User,
    reason_text: Optional[str] = None,
) -> SalaryRevision:
    rev = await get(db, revision_id)
    if rev.status != "pending_approval":
        raise ValidationError(f"Cannot reject a revision in {rev.status!r}")
    rev.status = "rejected"
    rev.approved_by = approver.id
    rev.approved_at = _now()
    if reason_text:
        rev.notes = (rev.notes or "") + f"\n[Rejected]: {reason_text}"
    await db.commit()
    await db.refresh(rev)
    return rev


async def cancel(
    db: AsyncSession, revision_id: int, *, actor: User
) -> SalaryRevision:
    rev = await get(db, revision_id)
    if rev.status not in ("draft", "pending_approval", "approved"):
        raise ValidationError("Already final")
    if rev.proposed_by != actor.id and not (
        set(actor.role_codes) & {"super_admin", "hr"}
    ):
        raise ForbiddenError("Only the proposer or HR can cancel")
    rev.status = "cancelled"
    await db.commit()
    await db.refresh(rev)
    return rev


async def apply(
    db: AsyncSession, revision_id: int, *, actor: User
) -> SalaryRevision:
    """Flip Employee.ctc_annual / template / designation + generate the
    increment letter PDF."""
    rev = await get(db, revision_id)
    if rev.status != "approved":
        raise ValidationError("Only approved revisions can be applied")
    if rev.effective_date > date.today():
        raise ValidationError(
            f"Cannot apply before effective_date ({rev.effective_date})"
        )

    emp = (
        await db.execute(
            select(Employee).where(Employee.id == rev.employee_id)
        )
    ).scalar_one()
    emp.ctc_annual = rev.new_ctc_annual
    if rev.new_salary_template_id:
        emp.salary_template_id = rev.new_salary_template_id
    if rev.new_designation_id:
        emp.designation_id = rev.new_designation_id

    rev.status = "applied"
    rev.applied_at = _now()

    # Generate the increment letter PDF + persist via the storage helper.
    from app.services.compensation_pdf import render_increment_letter
    from app.services.storage import upload_fileobj

    designation = None
    if emp.designation_id:
        designation = (
            await db.execute(
                select(Designation).where(Designation.id == emp.designation_id)
            )
        ).scalar_one_or_none()
    pdf_bytes = render_increment_letter(
        revision=rev, employee=emp, designation=designation
    )
    _, url = upload_fileobj(
        io.BytesIO(pdf_bytes),
        key_prefix=f"compensation/{emp.employee_code}",
        filename=f"increment-letter-{emp.employee_code}-"
        f"{rev.effective_date.isoformat()}.pdf",
        content_type="application/pdf",
    )
    rev.increment_letter_url = url
    await db.commit()
    await db.refresh(rev)
    return rev


# ── Reads ──────────────────────────────────────────────────────────
async def get(db: AsyncSession, revision_id: int) -> SalaryRevision:
    rev = (
        await db.execute(
            select(SalaryRevision).where(SalaryRevision.id == revision_id)
        )
    ).scalar_one_or_none()
    if not rev:
        raise NotFoundError("Salary revision not found")
    return rev


async def list_for_employee(
    db: AsyncSession, employee_id: int
) -> Sequence[SalaryRevision]:
    return (
        await db.execute(
            select(SalaryRevision)
            .where(SalaryRevision.employee_id == employee_id)
            .order_by(SalaryRevision.created_at.desc())
        )
    ).scalars().all()


async def list_pending_approval(db: AsyncSession) -> Sequence[SalaryRevision]:
    return (
        await db.execute(
            select(SalaryRevision)
            .where(SalaryRevision.status == "pending_approval")
            .order_by(SalaryRevision.created_at.desc())
        )
    ).scalars().all()


async def list_revisions(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
    from_date=None,
    to_date=None,
) -> Sequence[SalaryRevision]:
    stmt = select(SalaryRevision)
    if employee_id is not None:
        stmt = stmt.where(SalaryRevision.employee_id == employee_id)
    if status:
        stmt = stmt.where(SalaryRevision.status == status)
    if reason:
        stmt = stmt.where(SalaryRevision.reason == reason)
    if from_date is not None:
        stmt = stmt.where(SalaryRevision.effective_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(SalaryRevision.effective_date <= to_date)
    stmt = stmt.order_by(SalaryRevision.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def update_revision(
    db: AsyncSession, revision_id: int, *, payload: dict
) -> SalaryRevision:
    """Edit a draft / pending_approval revision. Approved / applied
    revisions are immutable."""
    rev = (
        await db.execute(
            select(SalaryRevision).where(SalaryRevision.id == revision_id)
        )
    ).scalar_one_or_none()
    if not rev:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Revision not found")
    if rev.status not in ("draft", "pending_approval"):
        from app.core.exceptions import ValidationError
        raise ValidationError(
            f"Cannot edit a revision in '{rev.status}' state"
        )
    allowed = {
        "new_ctc_annual", "effective_date", "reason", "notes",
        "new_salary_template_id", "new_designation_id",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(rev, k, v)
    # Recompute increment_pct if new_ctc_annual changed.
    if "new_ctc_annual" in payload and rev.previous_ctc_annual:
        from decimal import Decimal as _D
        prev = _D(str(rev.previous_ctc_annual))
        new = _D(str(rev.new_ctc_annual))
        if prev > 0:
            rev.increment_pct = ((new - prev) / prev * _D("100")).quantize(_D("0.01"))
    await db.commit()
    await db.refresh(rev)
    return rev

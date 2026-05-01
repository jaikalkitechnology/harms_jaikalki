"""Resignation / offboarding workflow."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import Employee, Resignation, User


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Default NDC checklist — items HR/IT must clear before final settlement.
DEFAULT_NDC: dict[str, bool] = {
    "assets_returned": False,
    "id_card_returned": False,
    "it_access_revoked": False,
    "knowledge_transfer_done": False,
    "manager_signoff": False,
    "hr_signoff": False,
    "exit_interview_done": False,
    "final_payslip_generated": False,
}


async def submit(
    db: AsyncSession,
    *,
    employee: Employee,
    proposed_last_working_day: date,
    reason: Optional[str],
    notice_period_days: int = 60,
) -> Resignation:
    today = _now().date()
    if proposed_last_working_day <= today:
        raise ValidationError("proposed_last_working_day must be in the future")

    existing = (
        await db.execute(
            select(Resignation)
            .where(Resignation.employee_id == employee.id)
            .where(
                Resignation.status.notin_(["rejected", "settled", "cancelled"])
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError(
            "An active resignation request already exists for this employee"
        )

    res = Resignation(
        employee_id=employee.id,
        requested_at=_now(),
        proposed_last_working_day=proposed_last_working_day,
        reason=reason,
        status="manager_review",
        notice_period_days=notice_period_days,
        ndc_checklist=DEFAULT_NDC.copy(),
    )
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res


async def manager_decision(
    db: AsyncSession,
    resignation_id: int,
    *,
    manager: User,
    manager_employee: Employee,
    accept: bool,
    comment: Optional[str] = None,
    actual_last_working_day: Optional[date] = None,
) -> Resignation:
    res = await get(db, resignation_id)
    if res.status != "manager_review":
        raise ValidationError(
            f"Cannot act on a resignation in '{res.status}'"
        )
    target = (
        await db.execute(select(Employee).where(Employee.id == res.employee_id))
    ).scalar_one_or_none()
    if not target:
        raise NotFoundError("Employee not found")
    if target.reporting_to != manager_employee.id:
        # HR/admins can act too
        if not (
            set(manager.role_codes)
            & {"super_admin", "director", "hr", "admin"}
        ):
            raise ForbiddenError(
                "Only the direct manager or HR can decide this resignation"
            )

    res.manager_decision_at = _now()
    res.manager_decision_by = manager.id
    res.manager_comment = comment
    if accept:
        res.status = "in_notice"
        res.actual_last_working_day = (
            actual_last_working_day or res.proposed_last_working_day
        )
    else:
        res.status = "rejected"
    await db.commit()
    await db.refresh(res)
    return res


async def update_ndc(
    db: AsyncSession,
    resignation_id: int,
    *,
    actor: User,
    updates: dict,
) -> Resignation:
    res = await get(db, resignation_id)
    if res.status not in ("in_notice", "ndc_pending"):
        raise ValidationError("NDC can only be updated during notice period")
    checklist = dict(res.ndc_checklist or DEFAULT_NDC)
    for k, v in updates.items():
        if k in checklist:
            checklist[k] = bool(v)
    res.ndc_checklist = checklist
    if all(checklist.values()):
        res.status = "cleared"
        res.hr_cleared_at = _now()
    elif res.status == "in_notice":
        res.status = "ndc_pending"
    await db.commit()
    await db.refresh(res)
    return res


async def settle(
    db: AsyncSession,
    resignation_id: int,
    *,
    actor: User,
    final_settlement_amount: int,
    exit_interview_notes: Optional[str] = None,
) -> Resignation:
    res = await get(db, resignation_id)
    if res.status != "cleared":
        raise ValidationError(
            "All NDC items must be cleared before final settlement"
        )
    res.final_settlement_amount = final_settlement_amount
    res.exit_interview_notes = exit_interview_notes
    res.final_settled_at = _now()
    res.status = "settled"

    # Mark employee as separated.
    emp = (
        await db.execute(
            select(Employee).where(Employee.id == res.employee_id)
        )
    ).scalar_one_or_none()
    if emp:
        emp.status = "separated"
        emp.exit_date = res.actual_last_working_day or _now().date()

    await db.commit()
    await db.refresh(res)
    return res


async def cancel(
    db: AsyncSession,
    resignation_id: int,
    *,
    employee: Employee,
) -> Resignation:
    res = await get(db, resignation_id)
    if res.employee_id != employee.id:
        raise ForbiddenError("Not your resignation")
    if res.status not in ("submitted", "manager_review"):
        raise ValidationError(
            "Can only cancel before manager has decided"
        )
    res.status = "cancelled"
    await db.commit()
    await db.refresh(res)
    return res


async def get(db: AsyncSession, resignation_id: int) -> Resignation:
    r = (
        await db.execute(
            select(Resignation).where(Resignation.id == resignation_id)
        )
    ).scalar_one_or_none()
    if not r:
        raise NotFoundError("Resignation not found")
    return r


async def list_for_employee(
    db: AsyncSession, employee_id: int
) -> Sequence[Resignation]:
    return (
        await db.execute(
            select(Resignation)
            .where(Resignation.employee_id == employee_id)
            .order_by(Resignation.requested_at.desc())
        )
    ).scalars().all()


async def list_pending(db: AsyncSession) -> Sequence[Resignation]:
    return (
        await db.execute(
            select(Resignation)
            .where(
                Resignation.status.in_(
                    ["manager_review", "in_notice", "ndc_pending", "cleared"]
                )
            )
            .order_by(Resignation.requested_at.asc())
        )
    ).scalars().all()

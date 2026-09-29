"""Employee onboarding lifecycle: Intern → Probation → Confirmation.

Each phase is tracked as an ``EmployeeProbation`` row (the table
predates this refactor; the ``phase`` column distinguishes intern from
probation). Phases can be extended before they end, and the final
confirmation flips ``Employee.is_on_probation = False`` +
``confirmation_date`` — the flag the leave service reads to decide
whether the employee may apply for non-sick leaves.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models import Employee, EmployeeProbation, User


DEFAULT_INTERN_MONTHS = 3
DEFAULT_PROBATION_MONTHS = 6


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add_months(base: date, months: int) -> date:
    y = base.year + (base.month - 1 + months) // 12
    m = (base.month - 1 + months) % 12 + 1
    from calendar import monthrange
    d = min(base.day, monthrange(y, m)[1])
    return date(y, m, d)


async def _open_phase(
    db: AsyncSession, employee_id: int, phase: str
) -> Optional[EmployeeProbation]:
    return (
        await db.execute(
            select(EmployeeProbation)
            .where(EmployeeProbation.employee_id == employee_id)
            .where(EmployeeProbation.phase == phase)
            .where(EmployeeProbation.status.in_(("in_progress", "extended")))
            .order_by(EmployeeProbation.id.desc())
        )
    ).scalars().first()


async def stage_of(
    db: AsyncSession, employee: Employee
) -> str:
    """Return one of ``intern`` / ``probation`` / ``confirmed`` based on
    the latest EmployeeProbation row + Employee flags."""
    if getattr(employee, "confirmation_date", None) and not employee.is_on_probation:
        return "confirmed"
    open_intern = await _open_phase(db, employee.id, "intern")
    if open_intern is not None:
        return "intern"
    open_prob = await _open_phase(db, employee.id, "probation")
    if open_prob is not None:
        return "probation"
    # Fallback — use the boolean flag on the employee row.
    return "probation" if employee.is_on_probation else "confirmed"


async def start_intern(
    db: AsyncSession,
    *,
    employee: Employee,
    start_date: date,
    months: int = DEFAULT_INTERN_MONTHS,
) -> EmployeeProbation:
    if await _open_phase(db, employee.id, "intern") is not None:
        raise ConflictError("An open internship already exists for this employee")
    end = _add_months(start_date, months)
    row = EmployeeProbation(
        employee_id=employee.id,
        phase="intern",
        probation_start_date=start_date,
        probation_end_date=end,
        status="in_progress",
    )
    db.add(row)
    employee.is_on_probation = True
    employee.confirmation_date = None
    await db.commit()
    await db.refresh(row)
    return row


async def extend_intern(
    db: AsyncSession,
    *,
    employee: Employee,
    extension_end: date,
    reason: Optional[str] = None,
) -> EmployeeProbation:
    row = await _open_phase(db, employee.id, "intern")
    if row is None:
        raise NotFoundError("No open internship to extend")
    row.is_extended = True
    row.extension_end_date = extension_end
    row.extension_reason = reason
    row.status = "extended"
    await db.commit()
    await db.refresh(row)
    return row


async def start_probation(
    db: AsyncSession,
    *,
    employee: Employee,
    start_date: date,
    months: int = DEFAULT_PROBATION_MONTHS,
) -> EmployeeProbation:
    """Close any open internship and open a probation phase."""
    intern = await _open_phase(db, employee.id, "intern")
    if intern is not None:
        # Interns transition into probation — close the intern row.
        intern.status = "confirmed"
        intern.confirmed_date = start_date
    if await _open_phase(db, employee.id, "probation") is not None:
        raise ConflictError("An open probation already exists for this employee")
    end = _add_months(start_date, months)
    row = EmployeeProbation(
        employee_id=employee.id,
        phase="probation",
        probation_start_date=start_date,
        probation_end_date=end,
        status="in_progress",
    )
    db.add(row)
    employee.is_on_probation = True
    employee.probation_end_date = end
    employee.confirmation_date = None
    await db.commit()
    await db.refresh(row)
    return row


async def extend_probation(
    db: AsyncSession,
    *,
    employee: Employee,
    extension_end: date,
    reason: Optional[str] = None,
) -> EmployeeProbation:
    row = await _open_phase(db, employee.id, "probation")
    if row is None:
        raise NotFoundError("No open probation to extend")
    row.is_extended = True
    row.extension_end_date = extension_end
    row.extension_reason = reason
    row.status = "extended"
    employee.probation_end_date = extension_end
    await db.commit()
    await db.refresh(row)
    return row


async def confirm(
    db: AsyncSession,
    *,
    employee: Employee,
    confirmed_on: date,
    actor: Optional[User] = None,
) -> EmployeeProbation:
    row = await _open_phase(db, employee.id, "probation")
    if row is None:
        row = await _open_phase(db, employee.id, "intern")
    if row is None:
        raise NotFoundError(
            "No open intern / probation phase to confirm. Start one first."
        )
    row.status = "confirmed"
    row.confirmed_date = confirmed_on
    if actor:
        row.confirmed_by = actor.id
    employee.is_on_probation = False
    employee.confirmation_date = confirmed_on
    await db.commit()
    await db.refresh(row)
    return row


async def list_history(
    db: AsyncSession, *, employee_id: int
) -> list[EmployeeProbation]:
    return list(
        (
            await db.execute(
                select(EmployeeProbation)
                .where(EmployeeProbation.employee_id == employee_id)
                .order_by(EmployeeProbation.probation_start_date, EmployeeProbation.id)
            )
        ).scalars().all()
    )

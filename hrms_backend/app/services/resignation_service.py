"""Resignation / offboarding workflow."""
from __future__ import annotations

import io
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


def separation_employee_status(separation_type: Optional[str]) -> str:
    """Employee.status value the admin list renders as a red badge."""
    return "terminated" if separation_type == "termination" else "resigned"


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


# ── Letter renderer (uses the Jaikalki letterhead) ─────────────────────
_DEFAULT_RESIGNATION_BODY = (
    "Dear {{first_name}},\n\n"
    "This is to formally acknowledge your resignation from the "
    "position of {{designation}} in {{department}} at Jaikalki "
    "Technology Pvt Ltd. Your resignation has been accepted, and "
    "your last working day with the company will be {{last_working_date}}.\n\n"
    "You are required to serve the notice period as per policy, "
    "complete pending hand-overs and return all company assets by "
    "your last working day. HR will coordinate the No-Dues process, "
    "final settlement and issuance of your relieving / experience "
    "letter thereafter.\n\n"
    "We appreciate your contribution and wish you the very best "
    "for your future endeavours.\n"
)

_DEFAULT_TERMINATION_BODY = (
    "Dear {{first_name}},\n\n"
    "This letter serves as formal notice that your employment with "
    "Jaikalki Technology Pvt Ltd as {{designation}} in {{department}} "
    "stands terminated with effect from {{last_working_date}}.\n\n"
    "Reason: {{reason}}\n\n"
    "You are required to clear all outstanding company assets, "
    "handovers and dues by your last working day. Your final "
    "settlement will be processed as per company policy and applicable "
    "statutory guidelines.\n\n"
    "For any queries relating to this notice or the settlement, "
    "please contact the Human Resources department.\n"
)


def render_separation_pdf(
    resignation: Resignation, employee: Employee
) -> bytes:
    """Render the resignation / termination letter over the branded
    Jaikalki letterhead so HR can print or attach it to an email."""
    from types import SimpleNamespace

    from app.services.letter_template_service import render_letter_pdf

    is_termination = resignation.separation_type == "termination"
    subject = (
        "Subject: Termination of Employment"
        if is_termination
        else "Subject: Acceptance of Resignation"
    )
    body = (
        _DEFAULT_TERMINATION_BODY if is_termination else _DEFAULT_RESIGNATION_BODY
    )
    template = SimpleNamespace(
        code=(
            "termination_letter" if is_termination else "resignation_acceptance"
        ),
        name=(
            "Termination Letter"
            if is_termination
            else "Resignation Acceptance Letter"
        ),
        category="termination" if is_termination else "other",
        subject=subject,
        body=body,
    )
    lwd = (
        resignation.actual_last_working_day
        or resignation.proposed_last_working_day
    )
    letter_no_prefix = "TL" if is_termination else "RL"
    letter_no = (
        f"JKT/HR/{letter_no_prefix}/{resignation.id:03d}/"
        f"{lwd.year if lwd else datetime.utcnow().year}"
    )
    return render_letter_pdf(
        template,
        employee,
        overrides={
            "letter_no": letter_no,
            "last_working_date": lwd.strftime("%d %b %Y") if lwd else "—",
            "reason": (resignation.reason or "—"),
        },
    )


async def admin_initiate(
    db: AsyncSession,
    *,
    employee: Employee,
    separation_type: str,
    proposed_last_working_day: date,
    reason: Optional[str],
    notice_period_days: int = 30,
    manager_comment: Optional[str] = None,
    actor: Optional[User] = None,
) -> Resignation:
    """Admin creates a resignation / termination on behalf of an
    employee and auto-approves it (skips the manager review step).

    Status lands as ``in_notice`` when the last-working-day is in the
    future; if the LWD is today or past we jump straight to ``cleared``
    so payroll can finalise the settlement. The employee's exit_date
    is set to the LWD so attendance clamps immediately (see the
    attendance service-window guard)."""

    if separation_type not in ("resignation", "termination"):
        raise ValidationError("separation_type must be resignation or termination")

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
            "An active resignation / termination already exists for this "
            "employee. Cancel or settle the existing one first."
        )

    today = _now().date()
    lwd_in_future = proposed_last_working_day > today
    status_ = "in_notice" if lwd_in_future else "cleared"

    res = Resignation(
        employee_id=employee.id,
        requested_at=_now(),
        proposed_last_working_day=proposed_last_working_day,
        actual_last_working_day=None if lwd_in_future else proposed_last_working_day,
        reason=reason,
        status=status_,
        separation_type=separation_type,
        notice_period_days=notice_period_days,
        manager_comment=manager_comment,
        # Admin action is the approval — stamp the decision as accepted.
        manager_decision_at=_now(),
        manager_decision_by=actor.id if actor else None,
        ndc_checklist=DEFAULT_NDC.copy(),
    )
    db.add(res)

    # Reflect the separation on the employee record so attendance,
    # payroll and the employee list all see it. Payroll keeps paying
    # resigned / terminated employees until exit_date passes.
    employee.exit_date = proposed_last_working_day
    employee.status = separation_employee_status(separation_type)
    # Lock any future self-service resignation attempts.
    employee.resignation_unlocked = False

    await db.commit()
    await db.refresh(res)
    return res


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

    # Gate: admin must unlock resignation submission for this employee
    # before the mobile app accepts a request.
    if not getattr(employee, "resignation_unlocked", False):
        raise ValidationError(
            "Resignation submission is locked. Please contact HR / admin to "
            "enable resignation requests for your account."
        )

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
    # Auto-lock again so the same employee can't submit a second time
    # without a fresh admin unlock.
    employee.resignation_unlocked = False
    await db.commit()
    await db.refresh(res)
    return res


async def set_resignation_unlock(
    db: AsyncSession,
    *,
    employee: Employee,
    unlocked: bool,
) -> Employee:
    employee.resignation_unlocked = bool(unlocked)
    await db.commit()
    await db.refresh(employee)
    return employee


async def manager_decision(
    db: AsyncSession,
    resignation_id: int,
    *,
    manager: User,
    manager_employee: Optional[Employee] = None,
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
    # HR / admin / director / super-admin can always decide, even when
    # they have no Employee row of their own. Otherwise the caller must
    # be the target's direct reporting manager.
    privileged = bool(
        set(manager.role_codes)
        & {"super_admin", "director", "hr", "admin"}
    )
    if not privileged:
        if manager_employee is None or target.reporting_to != manager_employee.id:
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
        # Also clamp the employee's exit_date so attendance / payroll
        # respect the last working day immediately (matches the admin-
        # initiated separation path).
        target.exit_date = res.actual_last_working_day
        target.status = separation_employee_status(
            getattr(res, "separation_type", "resignation")
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
        emp.status = separation_employee_status(
            getattr(res, "separation_type", "resignation")
        )
        emp.exit_date = res.actual_last_working_day or _now().date()
        # Release the held final salary.
        from app.services.payroll_service import set_final_payslips_hold

        await set_final_payslips_hold(db, emp.id, on_hold=False)

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


# ── Admin corrections: edit / undo / delete ───────────────────────────
_ACCEPTED_STATES = ("accepted", "in_notice", "ndc_pending", "cleared", "settled")


async def _employee_of(db: AsyncSession, res: Resignation) -> Optional[Employee]:
    return (
        await db.execute(select(Employee).where(Employee.id == res.employee_id))
    ).scalar_one_or_none()


def _restore_employee(emp: Employee) -> None:
    """Put a separated employee back on the roll."""
    if emp.status in ("resigned", "terminated", "separated", "inactive"):
        emp.status = "active"
    emp.exit_date = None


async def admin_update(
    db: AsyncSession,
    resignation_id: int,
    *,
    fields: dict,
) -> Resignation:
    """Edit a separation. When it's already accepted, keep the employee's
    exit_date / status in sync with the new values."""
    res = await get(db, resignation_id)
    if "separation_type" in fields and fields["separation_type"] not in (
        "resignation",
        "termination",
    ):
        raise ValidationError("separation_type must be resignation or termination")
    for key in (
        "separation_type",
        "proposed_last_working_day",
        "actual_last_working_day",
        "reason",
        "notice_period_days",
        "manager_comment",
    ):
        if key in fields:
            setattr(res, key, fields[key])

    if res.status in _ACCEPTED_STATES:
        emp = await _employee_of(db, res)
        if emp is not None:
            emp.exit_date = (
                res.actual_last_working_day or res.proposed_last_working_day
            )
            emp.status = separation_employee_status(res.separation_type)
    await db.commit()
    await db.refresh(res)
    return res


async def admin_undo(db: AsyncSession, resignation_id: int) -> dict:
    """Step the separation back one stage.

    settled                      → cleared   (settlement cleared)
    accepted / in_notice /
    ndc_pending / cleared /
    rejected                     → manager_review, employee back on roll
    """
    res = await get(db, resignation_id)
    if res.status == "settled":
        res.status = "cleared"
        res.final_settlement_amount = None
        res.final_settled_at = None
        res.exit_interview_notes = None
        from app.services.payroll_service import set_final_payslips_hold

        await set_final_payslips_hold(db, res.employee_id, on_hold=True)
        await db.commit()
        return {"action": "settlement_undone", "status": res.status}

    if res.status in ("accepted", "in_notice", "ndc_pending", "cleared", "rejected"):
        was = res.status
        res.status = "manager_review"
        res.manager_decision_at = None
        res.manager_decision_by = None
        res.actual_last_working_day = None
        res.hr_cleared_at = None
        emp = await _employee_of(db, res)
        if emp is not None:
            _restore_employee(emp)
        await db.commit()
        return {
            "action": "rejection_undone" if was == "rejected" else "decision_undone",
            "status": res.status,
        }

    raise ValidationError(
        f"Nothing to undo — this separation is '{res.status}'. "
        "Use Delete to remove it."
    )


async def admin_delete(db: AsyncSession, resignation_id: int) -> None:
    """Remove the separation record and put the employee back on roll."""
    res = await get(db, resignation_id)
    emp = await _employee_of(db, res)
    if emp is not None and res.status in _ACCEPTED_STATES:
        _restore_employee(emp)
    await db.delete(res)
    await db.commit()


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


async def list_resignations(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    search: Optional[str] = None,
    from_date=None,
    to_date=None,
) -> Sequence[Resignation]:
    from sqlalchemy import or_

    stmt = select(Resignation)
    if status:
        stmt = stmt.where(Resignation.status == status)
    if employee_id is not None:
        stmt = stmt.where(Resignation.employee_id == employee_id)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Resignation.reason.ilike(like),
                Resignation.manager_comment.ilike(like),
                Resignation.exit_interview_notes.ilike(like),
            )
        )
    if from_date is not None:
        stmt = stmt.where(Resignation.requested_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(Resignation.requested_at <= to_date)
    stmt = stmt.order_by(Resignation.requested_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_resignation(
    db: AsyncSession, resignation_id: int
) -> Resignation:
    res = (
        await db.execute(
            select(Resignation).where(Resignation.id == resignation_id)
        )
    ).scalar_one_or_none()
    if not res:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Resignation not found")
    return res


async def attach_document(
    db: AsyncSession,
    resignation_id: int,
    *,
    url: str,
    name: str,
    mime: Optional[str],
    size: int,
    kind: str = "other",
    uploaded_by: Optional[int] = None,
) -> Resignation:
    res = await get_resignation(db, resignation_id)
    docs = list(res.documents or [])
    docs.append(
        {
            "url": url,
            "name": name,
            "mime": mime,
            "size": size,
            "kind": kind,
            "uploaded_by": uploaded_by,
            "uploaded_at": _now().isoformat(),
        }
    )
    res.documents = docs
    await db.commit()
    await db.refresh(res)
    return res


async def remove_document(
    db: AsyncSession, resignation_id: int, *, index: int
) -> Resignation:
    res = await get_resignation(db, resignation_id)
    docs = list(res.documents or [])
    if 0 <= index < len(docs):
        docs.pop(index)
        res.documents = docs
        await db.commit()
        await db.refresh(res)
    return res

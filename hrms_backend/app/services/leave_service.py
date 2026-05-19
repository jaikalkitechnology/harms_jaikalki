"""Leave service: apply / approve / reject / balance / overlap detection."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    CompOff,
    Employee,
    Holiday,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    User,
)
from app.utils.leave_year import financial_year_start


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Helpers ───────────────────────────────────────────────────────────
def _count_working_days(
    from_date: date, to_date: date, holidays: set[date]
) -> Decimal:
    """Sundays + holidays don't count. Saturdays count (Jaikalki convention)."""
    if from_date > to_date:
        return Decimal("0")
    days = 0
    d = from_date
    while d <= to_date:
        if d.weekday() != 6 and d not in holidays:  # 6 == Sunday
            days += 1
        d = d + timedelta(days=1)
    return Decimal(days)


async def _get_holidays(
    db: AsyncSession, from_date: date, to_date: date
) -> set[date]:
    rows = (
        await db.execute(
            select(Holiday)
            .where(Holiday.date >= from_date)
            .where(Holiday.date <= to_date)
        )
    ).scalars().all()
    return {h.date for h in rows}


async def get_or_create_balance(
    db: AsyncSession, employee_id: int, leave_type: LeaveType, year: int
) -> LeaveBalance:
    bal = (
        await db.execute(
            select(LeaveBalance)
            .where(LeaveBalance.employee_id == employee_id)
            .where(LeaveBalance.leave_type_id == leave_type.id)
            .where(LeaveBalance.year == year)
        )
    ).scalar_one_or_none()
    if bal:
        return bal
    bal = LeaveBalance(
        employee_id=employee_id,
        leave_type_id=leave_type.id,
        year=year,
        allocated=leave_type.days_per_year,
        used=Decimal("0"),
        carried_forward=Decimal("0"),
    )
    db.add(bal)
    await db.flush()
    return bal


async def list_balances(
    db: AsyncSession, employee_id: int, year: Optional[int] = None
) -> Sequence[LeaveBalance]:
    year = year or financial_year_start(_today())
    types = (
        await db.execute(
            select(LeaveType).where(LeaveType.is_active.is_(True))
        )
    ).scalars().all()
    # Ensure a balance exists for every active leave type so the UI shows zeros.
    for t in types:
        await get_or_create_balance(db, employee_id, t, year)
    await db.flush()
    return (
        await db.execute(
            select(LeaveBalance)
            .where(LeaveBalance.employee_id == employee_id)
            .where(LeaveBalance.year == year)
            .order_by(LeaveBalance.leave_type_id)
        )
    ).scalars().all()


# ── Manual balance adjustment (audited) ─────────────────────────────
async def adjust_balance(
    db: AsyncSession,
    *,
    employee_id: int,
    leave_type_id: int,
    delta: Decimal | int | float,
    reason: str,
    actor: Optional[User] = None,
    year: Optional[int] = None,
) -> LeaveBalance:
    """Add (+) or remove (−) days from a leave balance and write an
    audited LeaveAdjustment row capturing who/why."""
    from app.models import LeaveAdjustment

    delta = Decimal(str(delta))
    if delta == 0:
        raise ValidationError("Adjustment cannot be zero")
    if not (reason or "").strip():
        raise ValidationError("A reason is required for any adjustment")

    fy = year or financial_year_start(_today())
    lt = (
        await db.execute(select(LeaveType).where(LeaveType.id == leave_type_id))
    ).scalar_one_or_none()
    if not lt:
        raise NotFoundError("Leave type not found")

    bal = await get_or_create_balance(db, employee_id, lt, fy)
    bal.adjustment = (bal.adjustment or Decimal("0")) + delta

    db.add(
        LeaveAdjustment(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=fy,
            delta=delta,
            reason=reason.strip(),
            created_by=actor.id if actor else None,
        )
    )
    await db.commit()
    await db.refresh(bal)
    return bal


async def list_adjustments(
    db: AsyncSession, employee_id: int, *, year: Optional[int] = None
) -> Sequence:
    from app.models import LeaveAdjustment

    stmt = (
        select(LeaveAdjustment)
        .where(LeaveAdjustment.employee_id == employee_id)
        .order_by(LeaveAdjustment.created_at.desc())
    )
    if year is not None:
        stmt = stmt.where(LeaveAdjustment.year == year)
    return (await db.execute(stmt)).scalars().all()


# ── Apply / cancel / decide ─────────────────────────────────────────
async def apply_leave(
    db: AsyncSession,
    employee: Employee,
    *,
    leave_type_id: int,
    from_date: date,
    to_date: date,
    reason: Optional[str],
    half_day: bool = False,
    attachment_url: Optional[str] = None,
) -> LeaveRequest:
    if from_date > to_date:
        raise ValidationError("from_date must be on or before to_date")
    if half_day and from_date != to_date:
        raise ValidationError("Half-day leave must be a single date")

    lt = (
        await db.execute(select(LeaveType).where(LeaveType.id == leave_type_id))
    ).scalar_one_or_none()
    if not lt or not lt.is_active:
        raise NotFoundError("Leave type not available")

    # Check overlap with existing pending/approved leaves.
    overlap = (
        await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee.id)
            .where(LeaveRequest.status.in_(["pending", "approved"]))
            .where(LeaveRequest.from_date <= to_date)
            .where(LeaveRequest.to_date >= from_date)
        )
    ).scalars().first()
    if overlap:
        raise ConflictError("Leave overlaps with an existing request")

    holidays = await _get_holidays(db, from_date, to_date)
    from app.services.leave_policy import count_leave_days, get_leave_policy

    policy = await get_leave_policy(db)
    days = count_leave_days(
        from_date,
        to_date,
        holidays,
        sandwich_enabled=bool(policy["sandwich_enabled"]),
        sandwich_count_holidays=bool(policy["sandwich_count_holidays"]),
    )
    if half_day:
        days = Decimal("0.5")
    if days <= 0:
        raise ValidationError("No working days in the selected range")

    # Check attachment requirement.
    if (
        lt.requires_attachment_after_days
        and days >= Decimal(lt.requires_attachment_after_days)
        and not attachment_url
    ):
        raise ValidationError(
            f"{lt.name} of {days} days requires a supporting document"
        )

    # Balance check. Leave-year is the Apr–Mar financial year.
    year = financial_year_start(from_date)
    bal = await get_or_create_balance(db, employee.id, lt, year)
    if bal.balance < days:
        raise ValidationError(
            f"Insufficient {lt.code} balance ({bal.balance} available, {days} requested)"
        )

    req = LeaveRequest(
        employee_id=employee.id,
        leave_type_id=lt.id,
        from_date=from_date,
        to_date=to_date,
        days=days,
        half_day=half_day,
        reason=reason,
        attachment_url=attachment_url,
        status="pending",
        applied_at=_now(),
    )
    db.add(req)
    await db.flush()

    # Mirror into the universal approval engine so this request appears in
    # the cross-module inbox.
    from app.services import approval_engine
    await approval_engine.submit_for_approval(
        db,
        request_type="leave_request",
        request_id=req.id,
        employee_id=employee.id,
        initiated_by=employee.user_id,
        title=(
            f"{lt.code} · {days} day(s) · "
            f"{employee.first_name} {employee.last_name}"
        ),
        summary=reason,
        request_data={
            "leave_type_code": lt.code,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "days": float(days),
            "half_day": half_day,
            "employee_code": employee.employee_code,
        },
    )

    await db.commit()
    await db.refresh(req)
    return req


async def cancel_leave(
    db: AsyncSession,
    request_id: int,
    *,
    employee: Employee,
) -> LeaveRequest:
    req = (
        await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("Leave request not found")
    if req.employee_id != employee.id:
        raise ForbiddenError("Cannot cancel someone else's leave")
    if req.status not in {"pending", "approved"}:
        raise ValidationError("Only pending/approved leaves can be cancelled")

    # Release balance if it had been deducted.
    if req.status == "approved":
        bal = await get_or_create_balance(
            db,
            req.employee_id,
            req.leave_type,
            financial_year_start(req.from_date),
        )
        bal.used = max(Decimal("0"), bal.used - req.days)

    req.status = "cancelled"
    req.approved_at = _now()
    await db.commit()
    await db.refresh(req)
    return req


async def list_my_requests(
    db: AsyncSession,
    employee_id: int,
    *,
    status: Optional[str] = None,
) -> Sequence[LeaveRequest]:
    stmt = (
        select(LeaveRequest)
        .where(LeaveRequest.employee_id == employee_id)
        .order_by(LeaveRequest.from_date.desc())
    )
    if status:
        stmt = stmt.where(LeaveRequest.status == status)
    return (await db.execute(stmt)).scalars().all()


async def list_pending_for_approver(
    db: AsyncSession,
    approver_user: User,
    *,
    visible_employee_ids: Optional[set[int]],
) -> Sequence[LeaveRequest]:
    stmt = (
        select(LeaveRequest)
        .where(LeaveRequest.status == "pending")
        .order_by(LeaveRequest.applied_at.desc())
    )
    if visible_employee_ids is not None:
        if not visible_employee_ids:
            return []
        stmt = stmt.where(LeaveRequest.employee_id.in_(visible_employee_ids))
    return (await db.execute(stmt)).scalars().all()


async def decide_leave(
    db: AsyncSession,
    request_id: int,
    *,
    approver: User,
    approve: bool,
    decision_comment: Optional[str] = None,
) -> LeaveRequest:
    req = (
        await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("Leave request not found")
    if req.status != "pending":
        raise ValidationError("Leave already decided")

    if approve:
        bal = await get_or_create_balance(
            db,
            req.employee_id,
            req.leave_type,
            financial_year_start(req.from_date),
        )
        if bal.balance < req.days:
            raise ValidationError(
                f"Cannot approve — only {bal.balance} {req.leave_type.code} left"
            )
        bal.used = bal.used + req.days
        req.status = "approved"
    else:
        req.status = "rejected"

    req.approver_id = approver.id
    req.approved_at = _now()
    req.decision_comment = decision_comment

    # Sync the universal approval row, if it exists.
    from app.services import approval_engine
    await approval_engine.mark_externally_decided(
        db,
        request_type="leave_request",
        request_id=req.id,
        approve=approve,
        decided_by=approver.id,
        comments=decision_comment,
    )

    await db.commit()
    await db.refresh(req)
    return req


async def list_requests_admin(
    db: AsyncSession,
    *,
    visible_employee_ids: Optional[set[int]],
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    leave_type_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Sequence[LeaveRequest]:
    """Approver-side list of every leave request (any status) within
    the caller's visible employee set, with optional filters."""
    stmt = select(LeaveRequest).order_by(LeaveRequest.applied_at.desc())
    if visible_employee_ids is not None:
        if not visible_employee_ids:
            return []
        stmt = stmt.where(LeaveRequest.employee_id.in_(visible_employee_ids))
    if status:
        stmt = stmt.where(LeaveRequest.status == status)
    if employee_id is not None:
        stmt = stmt.where(LeaveRequest.employee_id == employee_id)
    if leave_type_id is not None:
        stmt = stmt.where(LeaveRequest.leave_type_id == leave_type_id)
    if from_date is not None:
        stmt = stmt.where(LeaveRequest.to_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(LeaveRequest.from_date <= to_date)
    return (await db.execute(stmt)).scalars().all()


async def undo_decision(
    db: AsyncSession,
    request_id: int,
    *,
    approver: User,
) -> LeaveRequest:
    """Revert an approved/rejected leave back to pending so it can be
    re-decided. An approved leave's consumed balance is released."""
    req = (
        await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("Leave request not found")
    if req.status not in ("approved", "rejected"):
        raise ValidationError(
            f"Only an approved or rejected leave can be undone "
            f"(this one is '{req.status}')"
        )

    if req.status == "approved":
        bal = await get_or_create_balance(
            db,
            req.employee_id,
            req.leave_type,
            financial_year_start(req.from_date),
        )
        bal.used = max(Decimal("0"), bal.used - req.days)

    req.status = "pending"
    req.approver_id = None
    req.approved_at = None
    req.decision_comment = None

    # Best-effort: reopen the universal approval row if the engine
    # tracks one. Swallow errors so a missing mirror never blocks undo.
    try:
        from app.services import approval_engine

        reopen = getattr(approval_engine, "reopen_external", None)
        if reopen is not None:
            await reopen(
                db, request_type="leave_request", request_id=req.id
            )
    except Exception:
        pass

    await db.commit()
    await db.refresh(req)
    return req


# ── Calendar ──────────────────────────────────────────────────────────
async def team_calendar(
    db: AsyncSession,
    *,
    visible_employee_ids: Optional[set[int]],
    from_date: date,
    to_date: date,
) -> Sequence[LeaveRequest]:
    stmt = (
        select(LeaveRequest)
        .where(LeaveRequest.status == "approved")
        .where(LeaveRequest.from_date <= to_date)
        .where(LeaveRequest.to_date >= from_date)
        .order_by(LeaveRequest.from_date)
    )
    if visible_employee_ids is not None:
        if not visible_employee_ids:
            return []
        stmt = stmt.where(LeaveRequest.employee_id.in_(visible_employee_ids))
    return (await db.execute(stmt)).scalars().all()


# ── Comp-off ──────────────────────────────────────────────────────────
async def earn_comp_off(
    db: AsyncSession,
    employee: Employee,
    *,
    earned_date: date,
    days: Decimal = Decimal("1"),
    reason: Optional[str] = None,
) -> CompOff:
    expiry = earned_date + timedelta(days=90)
    co = CompOff(
        employee_id=employee.id,
        earned_date=earned_date,
        expiry_date=expiry,
        days=days,
        status="active",
        reason=reason,
    )
    db.add(co)
    await db.commit()
    await db.refresh(co)
    return co


async def list_comp_off(
    db: AsyncSession, employee_id: int
) -> Sequence[CompOff]:
    return (
        await db.execute(
            select(CompOff)
            .where(CompOff.employee_id == employee_id)
            .order_by(CompOff.earned_date.desc())
        )
    ).scalars().all()

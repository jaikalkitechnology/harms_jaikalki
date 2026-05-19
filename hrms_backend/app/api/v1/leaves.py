from datetime import date
from decimal import Decimal
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import (
    CompOff,
    Holiday,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    User,
)
from app.schemas.leave import (
    CalendarItem,
    CompOffEarn,
    CompOffOut,
    HolidayCreate,
    HolidayOut,
    LeaveAdjustmentOut,
    LeaveAdjustRequest,
    LeaveApplyRequest,
    LeaveBalanceOut,
    LeaveDecisionRequest,
    LeaveRequestOut,
    LeaveTypeOut,
)
from app.services import employee_service as emp_svc
from app.services import leave_service as leave_svc

router = APIRouter(prefix="/leaves", tags=["leaves"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ── Leave types ─────────────────────────────────────────────────────────
@router.get("/types", response_model=list[LeaveTypeOut])
async def list_leave_types(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        await db.execute(
            select(LeaveType).where(LeaveType.is_active.is_(True)).order_by(LeaveType.id)
        )
    ).scalars().all()


# ── Balances ────────────────────────────────────────────────────────────
@router.get("/balance", response_model=list[LeaveBalanceOut])
async def my_balance(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    rows = await leave_svc.list_balances(db, emp.id, year)
    out = []
    for b in rows:
        out.append(
            LeaveBalanceOut(
                id=b.id,
                employee_id=b.employee_id,
                leave_type_id=b.leave_type_id,
                leave_type=LeaveTypeOut.model_validate(b.leave_type) if b.leave_type else None,
                year=b.year,
                allocated=b.allocated,
                used=b.used,
                carried_forward=b.carried_forward,
                adjustment=b.adjustment,
                balance=b.balance,
            )
        )
    return out


@router.get(
    "/balance/{employee_id}",
    response_model=list[LeaveBalanceOut],
)
async def employee_balance(
    employee_id: int,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = await emp_svc.get_employee(db, employee_id)
    allowed = await emp_svc.visible_employee_ids(db, user)
    emp_svc.assert_can_view(user, target, allowed)
    rows = await leave_svc.list_balances(db, target.id, year)
    return [
        LeaveBalanceOut(
            id=b.id,
            employee_id=b.employee_id,
            leave_type_id=b.leave_type_id,
            leave_type=LeaveTypeOut.model_validate(b.leave_type) if b.leave_type else None,
            year=b.year,
            allocated=b.allocated,
            used=b.used,
            carried_forward=b.carried_forward,
            adjustment=b.adjustment,
            balance=b.balance,
        )
        for b in rows
    ]


@router.post(
    "/balance/{employee_id}/adjust",
    response_model=LeaveBalanceOut,
)
async def adjust_balance(
    employee_id: int,
    payload: LeaveAdjustRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    await emp_svc.get_employee(db, employee_id)
    b = await leave_svc.adjust_balance(
        db,
        employee_id=employee_id,
        leave_type_id=payload.leave_type_id,
        delta=payload.delta,
        reason=payload.reason,
        actor=user,
        year=payload.year,
    )
    return LeaveBalanceOut(
        id=b.id,
        employee_id=b.employee_id,
        leave_type_id=b.leave_type_id,
        leave_type=LeaveTypeOut.model_validate(b.leave_type)
        if b.leave_type
        else None,
        year=b.year,
        allocated=b.allocated,
        used=b.used,
        carried_forward=b.carried_forward,
        adjustment=b.adjustment,
        balance=b.balance,
    )


@router.get(
    "/balance/{employee_id}/adjustments",
    response_model=list[LeaveAdjustmentOut],
)
async def list_adjustments(
    employee_id: int,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    await emp_svc.get_employee(db, employee_id)
    return await leave_svc.list_adjustments(db, employee_id, year=year)


# ── Apply / cancel ──────────────────────────────────────────────────────
@router.post(
    "/apply",
    response_model=LeaveRequestOut,
    status_code=status.HTTP_201_CREATED,
)
async def apply_leave(
    payload: LeaveApplyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await leave_svc.apply_leave(
        db,
        emp,
        leave_type_id=payload.leave_type_id,
        from_date=payload.from_date,
        to_date=payload.to_date,
        reason=payload.reason,
        half_day=payload.half_day,
        attachment_url=payload.attachment_url,
    )


@router.get("/requests", response_model=list[LeaveRequestOut])
async def my_requests(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await leave_svc.list_my_requests(db, emp.id, status=status_filter)


@router.delete("/requests/{request_id}", response_model=LeaveRequestOut)
async def cancel_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await leave_svc.cancel_leave(db, request_id, employee=emp)


# ── Manager approvals ──────────────────────────────────────────────────
@router.get("/pending-approvals", response_model=list[LeaveRequestOut])
async def pending_approvals(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    visible = await emp_svc.visible_employee_ids(db, user)
    return await leave_svc.list_pending_for_approver(
        db, user, visible_employee_ids=visible
    )


@router.get("/all", response_model=list[LeaveRequestOut])
async def all_requests(
    status: Optional[str] = Query(default=None),
    employee_id: Optional[int] = Query(default=None),
    leave_type_id: Optional[int] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    visible = await emp_svc.visible_employee_ids(db, user)
    return await leave_svc.list_requests_admin(
        db,
        visible_employee_ids=visible,
        status=status,
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.post("/{request_id}/undo", response_model=LeaveRequestOut)
async def undo_leave_decision(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    return await leave_svc.undo_decision(db, request_id, approver=user)


@router.post("/{request_id}/approve", response_model=LeaveRequestOut)
async def approve_leave(
    request_id: int,
    payload: LeaveDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    return await leave_svc.decide_leave(
        db,
        request_id,
        approver=user,
        approve=True,
        decision_comment=payload.decision_comment,
    )


@router.post("/{request_id}/reject", response_model=LeaveRequestOut)
async def reject_leave(
    request_id: int,
    payload: LeaveDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("leave.approve.team")),
):
    return await leave_svc.decide_leave(
        db,
        request_id,
        approver=user,
        approve=False,
        decision_comment=payload.decision_comment,
    )


# ── Calendar ──────────────────────────────────────────────────────────
@router.get("/calendar", response_model=list[CalendarItem])
async def team_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    visible = await emp_svc.visible_employee_ids(db, user)
    rows = await leave_svc.team_calendar(
        db,
        visible_employee_ids=visible,
        from_date=from_date,
        to_date=to_date,
    )
    if not rows:
        return []
    # Lookup employees in one go.
    from app.models import Employee
    emp_ids = {r.employee_id for r in rows}
    emp_rows = (
        await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    ).scalars().all()
    emp_by_id = {e.id: e for e in emp_rows}
    out: list[CalendarItem] = []
    for r in rows:
        emp = emp_by_id.get(r.employee_id)
        if not emp:
            continue
        out.append(
            CalendarItem(
                employee_id=emp.id,
                employee_code=emp.employee_code,
                full_name=f"{emp.first_name} {emp.last_name}",
                from_date=r.from_date,
                to_date=r.to_date,
                leave_type=r.leave_type.code if r.leave_type else "—",
                days=r.days,
                status=r.status,
            )
        )
    return out


# ── Holidays ──────────────────────────────────────────────────────────
@router.get("/holidays", response_model=list[HolidayOut])
async def list_holidays(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Holiday).order_by(Holiday.date)
    if year:
        stmt = stmt.where(Holiday.date >= date(year, 1, 1)).where(
            Holiday.date <= date(year, 12, 31)
        )
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/holidays",
    response_model=HolidayOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_holiday(
    payload: HolidayCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = Holiday(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Holiday not found")
    await db.delete(obj)
    await db.commit()


# ── Comp-off ──────────────────────────────────────────────────────────
@router.post(
    "/comp-off/earn",
    response_model=CompOffOut,
    status_code=status.HTTP_201_CREATED,
)
async def earn_comp_off(
    payload: CompOffEarn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await leave_svc.earn_comp_off(
        db,
        emp,
        earned_date=payload.earned_date,
        days=payload.days,
        reason=payload.reason,
    )


@router.get("/comp-off/me", response_model=list[CompOffOut])
async def my_comp_offs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await leave_svc.list_comp_off(db, emp.id)

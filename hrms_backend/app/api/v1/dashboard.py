"""Role-aware dashboard summary endpoint.

Returns a single payload with widgets data; the mobile/admin clients pick
which widgets to render based on the user's role.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from app.config import settings
from app.core.permissions import Role as RoleEnum
from app.core.permissions import primary_role
from app.dependencies import get_current_user, get_db
from app.models import (
    Approval,
    Attendance,
    Employee,
    EmployeeCategory,
    LeaveRequest,
    User,
)
from app.schemas.dashboard import (
    BirthdayItem,
    DashboardOut,
    LeaveBalanceItem,
    ProbationExpiringItem,
    TeamMember,
    TodayAttendance,
)
from app.services import employee_service as emp_svc
from app.services import leave_service

router = APIRouter(tags=["dashboard"])


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _next_payday_days(today: Optional[date] = None) -> int:
    """Jaikalki convention: payday is the 1st of every month."""
    today = today or _today()
    if today.day == 1:
        return 0
    if today.month == 12:
        nxt = date(today.year + 1, 1, 1)
    else:
        nxt = date(today.year, today.month + 1, 1)
    return (nxt - today).days


@router.get("/dashboard/me", response_model=DashboardOut)
async def my_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardOut:
    today = _today()
    role = primary_role(user.role_codes)

    out = DashboardOut(
        role=role,
        role_level=user.max_role_level,
        user_full_name=user.full_name or user.email,
        employee_id=None,
        employee_code=None,
        company_name=settings.COMPANY_NAME,
        next_payday_in_days=_next_payday_days(today),
    )

    # ── Self employee + employee-shape widgets ────────────────────────
    self_emp = await emp_svc.get_self_employee(db, user)
    if self_emp:
        out.employee_id = self_emp.id
        out.employee_code = self_emp.employee_code

        att = (
            await db.execute(
                select(Attendance)
                .where(Attendance.employee_id == self_emp.id)
                .where(Attendance.date == today)
            )
        ).scalar_one_or_none()
        if att:
            out.today_attendance = TodayAttendance(
                checked_in=att.check_in is not None,
                checked_out=att.check_out is not None,
                check_in=att.check_in.isoformat() if att.check_in else None,
                check_out=att.check_out.isoformat() if att.check_out else None,
                status=att.status,
                work_mode=att.work_mode,
                distance_m=att.check_in_distance_m,
            )

        # Leave balances
        balances = await leave_service.list_balances(db, self_emp.id, today.year)
        out.leave_balances = [
            LeaveBalanceItem(
                code=b.leave_type.code if b.leave_type else "—",
                name=b.leave_type.name if b.leave_type else "Leave",
                balance=b.balance,
            )
            for b in balances
        ]

        # Pending leaves applied by self
        out.pending_self_leaves = (
            await db.execute(
                select(func.count(LeaveRequest.id))
                .where(LeaveRequest.employee_id == self_emp.id)
                .where(LeaveRequest.status == "pending")
            )
        ).scalar() or 0

    # ── Approver widgets ──────────────────────────────────────────────
    is_approver = bool(
        set(user.role_codes)
        & {
            RoleEnum.MANAGER.value,
            RoleEnum.HR.value,
            RoleEnum.ADMIN.value,
            RoleEnum.DIRECTOR.value,
            RoleEnum.SUPER_ADMIN.value,
        }
    )
    if is_approver:
        visible = await emp_svc.visible_employee_ids(db, user, scope="direct")
        approvals_stmt = (
            select(Approval).where(Approval.status == "pending")
        )
        if visible is not None:
            if visible:
                approvals_stmt = approvals_stmt.where(
                    Approval.employee_id.in_(visible)
                )
            else:
                approvals_stmt = approvals_stmt.where(False)
        pending_approvals = (await db.execute(approvals_stmt)).scalars().all()
        out.pending_approvals_count = len(pending_approvals)
        counts: dict[str, int] = {}
        for a in pending_approvals:
            counts[a.request_type] = counts.get(a.request_type, 0) + 1
        out.pending_by_type = [
            {"request_type": k, "count": v} for k, v in counts.items()
        ]

    # ── Manager-specific ──────────────────────────────────────────────
    if self_emp and (
        RoleEnum.MANAGER.value in user.role_codes
        or await emp_svc.has_reports(db, user)
    ):
        team = (
            await db.execute(
                select(Employee).where(Employee.reporting_to == self_emp.id)
            )
        ).scalars().all()
        out.team_size = len(team)
        if team:
            team_ids = [e.id for e in team]
            team_att = (
                await db.execute(
                    select(Attendance)
                    .where(Attendance.employee_id.in_(team_ids))
                    .where(Attendance.date == today)
                )
            ).scalars().all()
            att_by_emp = {a.employee_id: a for a in team_att}
            present = sum(
                1
                for a in team_att
                if a.status in ("present", "wfh", "half_day")
            )
            out.team_present_today = present
            out.team_attendance_pct = round((present / max(1, len(team))) * 100, 1)
            out.team_today = [
                TeamMember(
                    employee_id=e.id,
                    employee_code=e.employee_code,
                    full_name=f"{e.first_name} {e.last_name}",
                    status_today=(
                        att_by_emp[e.id].status if e.id in att_by_emp else "absent"
                    ),
                )
                for e in team
            ]

    # ── HR-specific ───────────────────────────────────────────────────
    if (
        RoleEnum.HR.value in user.role_codes
        or RoleEnum.SUPER_ADMIN.value in user.role_codes
    ):
        # Birthdays this week (any matching month/day in current week).
        week_end = today + timedelta(days=7)
        all_emps = (
            await db.execute(
                select(Employee).where(Employee.date_of_birth.is_not(None))
            )
        ).scalars().all()
        upcoming = []
        for e in all_emps:
            if not e.date_of_birth:
                continue
            this_year_bday = date(today.year, e.date_of_birth.month, e.date_of_birth.day)
            if today <= this_year_bday <= week_end:
                upcoming.append(
                    BirthdayItem(
                        employee_id=e.id,
                        employee_code=e.employee_code,
                        full_name=f"{e.first_name} {e.last_name}",
                        date_of_birth=e.date_of_birth,
                    )
                )
        out.birthdays_today = upcoming

        expiring = await emp_svc.expiring_probations(db, days=30)
        out.probation_expiring_30d = [
            ProbationExpiringItem(
                employee_id=e.id,
                employee_code=e.employee_code,
                full_name=f"{e.first_name} {e.last_name}",
                probation_end_date=e.probation_end_date,
                days_remaining=(e.probation_end_date - today).days,
            )
            for e in expiring
            if e.probation_end_date
        ]

    # ── Director-specific ─────────────────────────────────────────────
    if (
        RoleEnum.DIRECTOR.value in user.role_codes
        or RoleEnum.SUPER_ADMIN.value in user.role_codes
    ):
        out.total_headcount = (
            await db.execute(
                select(func.count(Employee.id)).where(Employee.status == "active")
            )
        ).scalar() or 0
        rows = (
            await db.execute(
                select(EmployeeCategory.code, func.count(Employee.id))
                .join(Employee, Employee.category_id == EmployeeCategory.id)
                .where(Employee.status == "active")
                .group_by(EmployeeCategory.code)
            )
        ).all()
        out.headcount_by_category = [
            {"category": r[0], "count": r[1]} for r in rows
        ]

    return out

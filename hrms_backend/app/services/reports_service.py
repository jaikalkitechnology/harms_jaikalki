"""Reports & analytics: cross-module aggregations + saved reports."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import (
    Attendance,
    Course,
    CourseEnrollment,
    Department,
    Employee,
    Lead,
    PayrollRun,
    Payslip,
    PerformanceReview,
    ReviewCycle,
    SalesOrder,
    SavedReport,
    TrainingSession,
    SessionParticipant,
    Quote,
    Verification,
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


# ── Headcount ────────────────────────────────────────────────────────
async def headcount_trend(
    db: AsyncSession, *, months: int = 12
) -> dict:
    employees = (await db.execute(select(Employee))).scalars().all()
    today = _today()
    start = date(today.year, today.month, 1) - timedelta(days=30 * (months - 1))
    start = date(start.year, start.month, 1)

    # Build month-by-month series.
    points = []
    cursor = start
    while cursor <= today:
        month_end = date(
            cursor.year,
            cursor.month,
            monthrange(cursor.year, cursor.month)[1],
        )
        joined = sum(
            1
            for e in employees
            if e.date_of_joining
            and e.date_of_joining.year == cursor.year
            and e.date_of_joining.month == cursor.month
        )
        exited = sum(
            1
            for e in employees
            if e.exit_date
            and e.exit_date.year == cursor.year
            and e.exit_date.month == cursor.month
        )
        active = sum(
            1
            for e in employees
            if e.date_of_joining
            and e.date_of_joining <= month_end
            and (e.exit_date is None or e.exit_date > month_end)
        )
        points.append(
            {
                "period": _month_key(cursor),
                "headcount": active,
                "joined": joined,
                "exited": exited,
            }
        )
        next_year = cursor.year + (1 if cursor.month == 12 else 0)
        next_month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = date(next_year, next_month, 1)

    current_headcount = sum(
        1 for e in employees if e.status == "active" and e.exit_date is None
    )
    return {
        "months": months,
        "points": points,
        "current_headcount": current_headcount,
    }


async def attrition_stats(
    db: AsyncSession, *, months: int = 12
) -> dict:
    today = _today()
    start = date(today.year, today.month, 1) - timedelta(days=30 * months)
    employees = (await db.execute(select(Employee))).scalars().all()
    starting_headcount = sum(
        1
        for e in employees
        if e.date_of_joining and e.date_of_joining < start
        and (e.exit_date is None or e.exit_date >= start)
    )
    exits = sum(
        1
        for e in employees
        if e.exit_date and start <= e.exit_date <= today
    )
    pct = (exits / starting_headcount * 100) if starting_headcount else 0.0
    return {
        "period_months": months,
        "starting_headcount": starting_headcount,
        "exits": exits,
        "attrition_pct": round(pct, 2),
    }


async def department_breakdown(
    db: AsyncSession,
) -> list[dict]:
    rows = (
        await db.execute(
            select(Department.name, func.count(Employee.id))
            .join(Employee, Employee.department_id == Department.id)
            .where(Employee.status == "active")
            .group_by(Department.name)
        )
    ).all()
    out = [{"department": name or "Unassigned", "headcount": count} for name, count in rows]
    out.sort(key=lambda r: r["headcount"], reverse=True)
    return out


# ── Attendance ───────────────────────────────────────────────────────
async def attendance_snapshot(
    db: AsyncSession, *, on_date: Optional[date] = None
) -> dict:
    target = on_date or _today()
    total = (
        await db.execute(
            select(func.count(Employee.id)).where(Employee.status == "active")
        )
    ).scalar() or 0
    rows = (
        await db.execute(
            select(Attendance.status, func.count(Attendance.id))
            .where(Attendance.date == target)
            .group_by(Attendance.status)
        )
    ).all()
    by_status = {s: c for s, c in rows}
    present = by_status.get("present", 0) + by_status.get("half_day", 0)
    wfh = by_status.get("wfh", 0)
    leave = by_status.get("leave", 0)
    holiday = by_status.get("holiday", 0)
    absent = max(0, total - present - wfh - leave - holiday)
    return {
        "on_date": target,
        "present": present,
        "wfh": wfh,
        "leave": leave,
        "absent": absent,
        "holiday": holiday,
        "total_employees": total,
    }


# ── Payroll ──────────────────────────────────────────────────────────
async def payroll_cost(
    db: AsyncSession, *, year: int, month: int
) -> Optional[dict]:
    run = (
        await db.execute(
            select(PayrollRun)
            .where(PayrollRun.year == year)
            .where(PayrollRun.month == month)
            .order_by(PayrollRun.id.desc())
        )
    ).scalar_one_or_none()
    if not run:
        return None
    payslips = (
        await db.execute(
            select(Payslip).where(Payslip.payroll_run_id == run.id)
        )
    ).scalars().all()
    if not payslips:
        return None
    gross = sum((p.gross or Decimal("0") for p in payslips), Decimal("0"))
    net = sum((p.net_pay or Decimal("0") for p in payslips), Decimal("0"))
    employer = sum(
        ((p.pf_employer or Decimal("0")) + (p.esic_employer or Decimal("0"))
         for p in payslips),
        Decimal("0"),
    )
    employer_cost = gross + employer
    avg = (employer_cost / len(payslips)).quantize(Decimal("0.01"))
    return {
        "year": year,
        "month": month,
        "total_gross": gross,
        "total_net": net,
        "total_employer_cost": employer_cost,
        "employee_count": len(payslips),
        "avg_cost_per_employee": avg,
    }


# ── Compliance ───────────────────────────────────────────────────────
async def compliance_overview(db: AsyncSession) -> dict:
    mandatory = (
        await db.execute(
            select(Course)
            .where(Course.is_mandatory.is_(True))
            .where(Course.is_published.is_(True))
        )
    ).scalars().all()
    mandatory_ids = [c.id for c in mandatory]
    employees_total = (
        await db.execute(
            select(func.count(Employee.id)).where(Employee.status == "active")
        )
    ).scalar() or 0
    if not mandatory_ids or employees_total == 0:
        return {
            "mandatory_courses": len(mandatory_ids),
            "employees_total": employees_total,
            "fully_compliant": 0,
            "partially_compliant": 0,
            "non_compliant": employees_total,
            "coverage_pct": 0.0,
        }

    # employee_id → set(completed mandatory course ids)
    rows = (
        await db.execute(
            select(CourseEnrollment.employee_id, CourseEnrollment.course_id)
            .where(CourseEnrollment.status == "completed")
            .where(CourseEnrollment.course_id.in_(mandatory_ids))
        )
    ).all()
    by_emp: dict[int, set[int]] = {}
    for emp_id, course_id in rows:
        by_emp.setdefault(emp_id, set()).add(course_id)

    employees = (
        await db.execute(
            select(Employee.id).where(Employee.status == "active")
        )
    ).scalars().all()
    fully = 0
    partial = 0
    none = 0
    for emp_id in employees:
        completed = by_emp.get(emp_id, set())
        if len(completed) == len(mandatory_ids):
            fully += 1
        elif completed:
            partial += 1
        else:
            none += 1
    coverage = (fully / employees_total * 100) if employees_total else 0.0
    return {
        "mandatory_courses": len(mandatory_ids),
        "employees_total": employees_total,
        "fully_compliant": fully,
        "partially_compliant": partial,
        "non_compliant": none,
        "coverage_pct": round(coverage, 2),
    }


# ── Sales ────────────────────────────────────────────────────────────
async def sales_overview(
    db: AsyncSession,
    *,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> dict:
    today = _today()
    end = period_end or today
    start = period_start or (end - timedelta(days=90))
    leads = (
        await db.execute(
            select(Lead)
            .where(Lead.created_at >= datetime.combine(start, datetime.min.time()))
            .where(Lead.created_at <= datetime.combine(end, datetime.max.time()))
        )
    ).scalars().all()
    leads_count = len(leads)
    won = sum(1 for l in leads if l.stage == "won")
    win_rate = (won / leads_count * 100) if leads_count else 0.0

    quotes = (
        await db.execute(
            select(func.coalesce(func.sum(Quote.total_amount), 0))
            .where(Quote.created_at >= datetime.combine(start, datetime.min.time()))
            .where(Quote.created_at <= datetime.combine(end, datetime.max.time()))
        )
    ).scalar() or Decimal("0")
    orders = (
        await db.execute(
            select(func.coalesce(func.sum(SalesOrder.total_amount), 0))
            .where(SalesOrder.placed_at >= datetime.combine(start, datetime.min.time()))
            .where(SalesOrder.placed_at <= datetime.combine(end, datetime.max.time()))
        )
    ).scalar() or Decimal("0")

    return {
        "period_start": start,
        "period_end": end,
        "leads_count": leads_count,
        "leads_won": won,
        "win_rate_pct": round(win_rate, 2),
        "quotes_total": Decimal(quotes),
        "orders_total": Decimal(orders),
    }


# ── Performance ──────────────────────────────────────────────────────
async def performance_overview(
    db: AsyncSession, *, cycle_id: Optional[int] = None
) -> Optional[dict]:
    cycle = None
    if cycle_id is not None:
        cycle = (
            await db.execute(
                select(ReviewCycle).where(ReviewCycle.id == cycle_id)
            )
        ).scalar_one_or_none()
    else:
        cycle = (
            await db.execute(
                select(ReviewCycle)
                .where(ReviewCycle.status.in_(["open", "review", "calibration"]))
                .order_by(ReviewCycle.period_start.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if not cycle:
        return None

    active_employees = (
        await db.execute(
            select(func.count(Employee.id)).where(Employee.status == "active")
        )
    ).scalar() or 0

    self_submitted = (
        await db.execute(
            select(func.count(PerformanceReview.id))
            .where(PerformanceReview.cycle_id == cycle.id)
            .where(PerformanceReview.review_type == "self")
            .where(PerformanceReview.status != "draft")
        )
    ).scalar() or 0
    manager_submitted = (
        await db.execute(
            select(func.count(PerformanceReview.id))
            .where(PerformanceReview.cycle_id == cycle.id)
            .where(PerformanceReview.review_type == "manager")
            .where(PerformanceReview.status != "draft")
        )
    ).scalar() or 0

    return {
        "cycle_id": cycle.id,
        "cycle_name": cycle.name,
        "self_reviews_submitted": self_submitted,
        "manager_reviews_submitted": manager_submitted,
        "pending_self_reviews": max(0, active_employees - self_submitted),
        "pending_manager_reviews": max(0, active_employees - manager_submitted),
    }


# ── Verification & training ──────────────────────────────────────────
async def verification_stats(db: AsyncSession) -> dict:
    rows = (
        await db.execute(
            select(Verification.status, func.count(Verification.id))
            .group_by(Verification.status)
        )
    ).all()
    by_status = {s: c for s, c in rows}
    total = sum(by_status.values())
    completed = by_status.get("completed", 0)
    in_progress = by_status.get("in_progress", 0)
    audit_pending = by_status.get("audit_pending", 0)

    completed_rows = (
        await db.execute(
            select(Verification).where(Verification.status == "completed")
        )
    ).scalars().all()
    durations = []
    breached = 0
    for v in completed_rows:
        end = v.audited_at or v.submitted_at
        if end:
            durations.append((end - v.assigned_at).total_seconds() / 3600)
            if v.deadline_at and end > v.deadline_at:
                breached += 1
    avg_hours = round(sum(durations) / len(durations), 2) if durations else 0.0
    breach_pct = (
        round(breached / len(completed_rows) * 100, 2) if completed_rows else 0.0
    )
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "audit_pending": audit_pending,
        "breach_pct": breach_pct,
        "avg_hours": avg_hours,
    }


async def training_stats(db: AsyncSession) -> dict:
    sessions = (await db.execute(select(TrainingSession))).scalars().all()
    completed = sum(1 for s in sessions if s.status == "completed")
    upcoming = sum(
        1
        for s in sessions
        if s.scheduled_start
        >= datetime.utcnow()
        and s.status != "cancelled"
    )
    attendees = (
        await db.execute(
            select(func.count(SessionParticipant.id)).where(
                SessionParticipant.status.in_(["attended", "completed"])
            )
        )
    ).scalar() or 0
    return {
        "sessions_total": len(sessions),
        "sessions_completed": completed,
        "upcoming_sessions": upcoming,
        "total_attendees": attendees,
    }


# ── Director dashboard (composite) ───────────────────────────────────
async def director_dashboard(db: AsyncSession) -> dict:
    today = _today()
    return {
        "headcount": await headcount_trend(db, months=12),
        "attrition": await attrition_stats(db, months=12),
        "department_breakdown": await department_breakdown(db),
        "payroll_this_month": await payroll_cost(
            db, year=today.year, month=today.month
        ),
        "compliance": await compliance_overview(db),
        "sales": await sales_overview(db),
        "verification": await verification_stats(db),
        "training": await training_stats(db),
    }


# ── Saved reports ────────────────────────────────────────────────────
async def create_saved_report(
    db: AsyncSession, *, payload: dict, created_by: Optional[int]
) -> SavedReport:
    if (
        await db.execute(
            select(SavedReport).where(SavedReport.code == payload["code"])
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Saved report '{payload['code']}' already exists")
    report = SavedReport(**payload, created_by=created_by)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_saved_reports(
    db: AsyncSession,
    *,
    user_id: int,
    include_shared: bool = True,
) -> Sequence[SavedReport]:
    stmt = select(SavedReport)
    if include_shared:
        stmt = stmt.where(
            or_(SavedReport.created_by == user_id, SavedReport.is_shared.is_(True))
        )
    else:
        stmt = stmt.where(SavedReport.created_by == user_id)
    stmt = stmt.order_by(SavedReport.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def delete_saved_report(
    db: AsyncSession, report_id: int, *, user_id: int
) -> None:
    report = (
        await db.execute(select(SavedReport).where(SavedReport.id == report_id))
    ).scalar_one_or_none()
    if not report:
        raise NotFoundError("Report not found")
    if report.created_by != user_id:
        from app.core.exceptions import ForbiddenError

        raise ForbiddenError("Only the creator can delete a saved report")
    await db.delete(report)
    await db.commit()

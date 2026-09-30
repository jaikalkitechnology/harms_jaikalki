"""Day-class breakdown for one employee, one calendar month.

Drives Loss-Of-Pay scaling in `payroll_service.process_payroll`. Each
day in the month gets exactly one of these classes (priority order):

    holiday    — a Holiday row covers the date (any location).
    week_off   — Sunday (Jaikalki convention; Saturday is a working day).
    paid_leave — approved LeaveRequest of an `is_paid` LeaveType.
    unpaid_leave — approved LeaveRequest of a non-paid type, OR a
                   sandwich Sunday/holiday between two unpaid days
                   when the leave type's `applies_sandwich_rule` is
                   set. Sandwich days are also tallied separately.
    present    — an Attendance row with status present/wfh/half_day.
    absent     — anything left over (no attendance, no leave, on a
                 working day).

Outputs Decimal counters because half-day attendance contributes 0.5.

Loss of Pay = days_unpaid_leave + days_absent.
Paid days  = working_days - LOP.

Sandwich rule (only applies to leave types flagged
`applies_sandwich_rule`, and only ever pulls *non-working* days into
LOP — actual working days that fall between two LWP days were already
classified as LWP by the LeaveRequest itself):

    LWP on Friday + LWP on Monday → the Saturday is a working day so
    it'd be classified by attendance/absent; the Sunday in between is
    a week-off but gets reclassified as unpaid_leave (sandwich).
"""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attendance, Holiday, LeaveRequest, LeaveType


@dataclass
class AttendanceMonth:
    year: int
    month: int
    working_days: Decimal = Decimal("0")
    days_present: Decimal = Decimal("0")
    days_paid_leave: Decimal = Decimal("0")
    days_unpaid_leave: Decimal = Decimal("0")
    days_absent: Decimal = Decimal("0")
    days_holiday: Decimal = Decimal("0")
    days_weekoff: Decimal = Decimal("0")
    days_sandwich: Decimal = Decimal("0")
    # Days in the attendance window that fall before date_of_joining or
    # after exit_date. They are neither worked nor absent.
    days_not_in_service: Decimal = Decimal("0")
    # Attendance window actually used (cycle-aware).
    window_first: Optional[date] = None
    window_last: Optional[date] = None
    window_days: int = 0

    # Per-day class for debugging / payslip annotation.
    by_date: dict[date, str] = field(default_factory=dict)

    @property
    def days_lop(self) -> Decimal:
        return self.days_unpaid_leave + self.days_absent

    @property
    def days_on_roll(self) -> Decimal:
        """Calendar days of the window the employee was employed."""
        return Decimal(self.window_days) - self.days_not_in_service

    @property
    def days_paid(self) -> Decimal:
        # Holidays + week-offs + present + paid leave + 0.5 of half-days
        # are all paid. We count this as (working_days - LOP) because
        # weekoffs/holidays don't enter the divisor either.
        return self.working_days - self.days_lop


def cycle_window(year: int, month: int, cycle_start_day: int = 1) -> tuple[date, date]:
    """Attendance window that feeds the payroll for ``year``/``month``.

    cycle_start_day 1  → calendar month (1st → last day).
    cycle_start_day N  → N of previous month → (N-1) of this month,
                         e.g. 21 → 21-Aug … 20-Sep for September.
    """
    if cycle_start_day and cycle_start_day > 1:
        prev_year = year if month > 1 else year - 1
        prev_month = month - 1 if month > 1 else 12
        start_day = min(cycle_start_day, monthrange(prev_year, prev_month)[1])
        end_day = min(cycle_start_day - 1, monthrange(year, month)[1])
        return date(prev_year, prev_month, start_day), date(year, month, end_day)
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def _is_sunday(d: date) -> bool:
    # Mon=0 ... Sun=6. Jaikalki's standard week-off is Sunday only.
    return d.weekday() == 6


async def compute_attendance_month(
    db: AsyncSession,
    employee_id: int,
    *,
    year: int,
    month: int,
    cycle_start_day: int = 1,
    treat_all_leave_as_paid: bool = True,
    sandwich_absent: bool = True,
    service_from: Optional[date] = None,
    service_to: Optional[date] = None,
) -> AttendanceMonth:
    first, last = cycle_window(year, month, cycle_start_day)
    days_in_month = (last - first).days + 1

    # Holidays for the month — match by date (any location).
    holidays: set[date] = {
        h.date for h in (
            await db.execute(
                select(Holiday).where(Holiday.date >= first).where(Holiday.date <= last)
            )
        ).scalars().all()
    }

    # Leaves overlapping the month. We pick up both approved AND pending
    # requests: a pending leave is in flight with HR and the employee
    # has *applied* — counting that day as "absent" and deducting salary
    # would punish the employee for HR's queue depth. Rejected /
    # cancelled requests are excluded; re-run payroll after rejection to
    # claw back the day.
    leaves: Sequence[LeaveRequest] = (
        await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee_id)
            .where(LeaveRequest.status.in_(("approved", "pending")))
            .where(LeaveRequest.from_date <= last)
            .where(LeaveRequest.to_date >= first)
        )
    ).scalars().all()

    # Map every leave-day in the month to (is_paid, applies_sandwich, half_day).
    # When ``treat_all_leave_as_paid`` is set (the Jaikalki default),
    # every approved leave is paid — the LeaveType.is_paid flag is
    # ignored for LOP/payroll purposes. Only "absent" attendance and the
    # absent half of a half-day mark deduct salary.
    leave_day: dict[date, tuple[bool, bool, bool]] = {}
    for lr in leaves:
        lt: LeaveType = lr.leave_type
        is_paid = True if treat_all_leave_as_paid else bool(getattr(lt, "is_paid", True))
        sandwich = (
            False
            if treat_all_leave_as_paid
            else bool(getattr(lt, "applies_sandwich_rule", False))
        )
        d = max(lr.from_date, first)
        end = min(lr.to_date, last)
        while d <= end:
            # If a paid leave already claims the day, don't downgrade
            # it to unpaid. Otherwise prefer the more-restrictive flag.
            prior = leave_day.get(d)
            if prior is None or (prior[0] and not is_paid):
                leave_day[d] = (is_paid, sandwich, bool(lr.half_day))
            d = d + timedelta(days=1)

    # Apply sandwich rule: walk across the month and flip any
    # week-off/holiday flanked by unpaid leave with applies_sandwich
    # into an unpaid-leave (sandwich) day.
    sandwich_days: set[date] = set()
    for i in range(days_in_month):
        d = first + timedelta(days=i)
        if d in leave_day:
            continue
        if not (_is_sunday(d) or d in holidays):
            continue
        # Look back for the nearest non-off-non-holiday day.
        prev = d - timedelta(days=1)
        while prev >= first and (_is_sunday(prev) or prev in holidays):
            prev -= timedelta(days=1)
        # Look forward similarly.
        nxt = d + timedelta(days=1)
        while nxt <= last and (_is_sunday(nxt) or nxt in holidays):
            nxt += timedelta(days=1)
        if prev < first or nxt > last:
            # Bracket runs off the month edge — skip; sandwich only
            # applies when both flanks are inside the period.
            continue
        prev_l = leave_day.get(prev)
        nxt_l = leave_day.get(nxt)
        if (
            prev_l and not prev_l[0] and prev_l[1]
            and nxt_l and not nxt_l[0] and nxt_l[1]
        ):
            sandwich_days.add(d)

    # Attendance rows for the month.
    att_by_date: dict[date, Attendance] = {
        a.date: a
        for a in (
            await db.execute(
                select(Attendance)
                .where(Attendance.employee_id == employee_id)
                .where(Attendance.date >= first)
                .where(Attendance.date <= last)
            )
        ).scalars().all()
    }

    out = AttendanceMonth(
        year=year,
        month=month,
        window_first=first,
        window_last=last,
        window_days=days_in_month,
    )

    for i in range(days_in_month):
        d = first + timedelta(days=i)
        # Before joining / after exit: not worked, not absent, not paid.
        if (service_from is not None and d < service_from) or (
            service_to is not None and d > service_to
        ):
            out.days_not_in_service += Decimal("1")
            out.by_date[d] = "not_in_service"
            continue
        is_holiday = d in holidays
        is_weekoff = _is_sunday(d)
        leave_info = leave_day.get(d)
        is_sandwich = d in sandwich_days

        if leave_info is not None:
            is_paid, _, half = leave_info
            if not (is_holiday or is_weekoff):
                out.working_days += Decimal("1")
            if not half:
                if is_paid:
                    out.days_paid_leave += Decimal("1")
                    out.by_date[d] = "paid_leave"
                else:
                    out.days_unpaid_leave += Decimal("1")
                    out.by_date[d] = "unpaid_leave"
                continue
            # Half-day leave: the other 0.5 of the day comes from
            # attendance (present/wfh ⇒ paid; otherwise ⇒ absent).
            half_inc = Decimal("0.5")
            if is_paid:
                out.days_paid_leave += half_inc
            else:
                out.days_unpaid_leave += half_inc
            att = att_by_date.get(d)
            if att and att.status in ("present", "wfh"):
                out.days_present += half_inc
                out.by_date[d] = (
                    "paid_leave_half+present" if is_paid
                    else "unpaid_leave_half+present"
                )
            else:
                out.days_absent += half_inc
                out.by_date[d] = (
                    "paid_leave_half+absent" if is_paid
                    else "unpaid_leave_half+absent"
                )
            continue

        if is_sandwich:
            out.days_unpaid_leave += Decimal("1")
            out.days_sandwich += Decimal("1")
            out.working_days += Decimal("1")
            out.by_date[d] = "unpaid_leave_sandwich"
            continue

        if is_holiday:
            out.days_holiday += Decimal("1")
            out.by_date[d] = "holiday"
            continue
        if is_weekoff:
            out.days_weekoff += Decimal("1")
            out.by_date[d] = "week_off"
            continue

        out.working_days += Decimal("1")
        att = att_by_date.get(d)
        if att and att.status in ("present", "wfh"):
            out.days_present += Decimal("1")
            out.by_date[d] = "present"
        elif att and att.status == "half_day":
            out.days_present += Decimal("0.5")
            out.days_absent += Decimal("0.5")
            out.by_date[d] = "half_day"
        elif att and att.status == "leave":
            # HR / admin marked the day as "leave" directly on the
            # attendance grid (no LeaveRequest row was opened). Honour
            # that mark — count it as a paid leave instead of letting
            # it slide into "absent" and deducting salary.
            out.days_paid_leave += Decimal("1")
            out.by_date[d] = "paid_leave_manual"
        else:
            out.days_absent += Decimal("1")
            out.by_date[d] = "absent"

    # Absence-sandwich pass: a Sunday / public holiday flanked by
    # "absent" working days on both sides is reclassified as absent.
    # Mirrors the unpaid-leave-sandwich math: bump days_absent AND
    # working_days so paid = working - LOP still cancels the day from
    # the divisor of the scaling ratio.
    if sandwich_absent:
        non_working = {"holiday", "week_off"}
        for i in range(days_in_month):
            d = first + timedelta(days=i)
            if out.by_date.get(d) not in non_working:
                continue
            # Nearest working-side classification on each flank.
            prev = d - timedelta(days=1)
            while prev >= first and out.by_date.get(prev) in non_working:
                prev -= timedelta(days=1)
            nxt = d + timedelta(days=1)
            while nxt <= last and out.by_date.get(nxt) in non_working:
                nxt += timedelta(days=1)
            if prev < first or nxt > last:
                continue  # Bracket runs off the cycle window.
            if (
                out.by_date.get(prev) == "absent"
                and out.by_date.get(nxt) == "absent"
            ):
                was = out.by_date[d]
                if was == "holiday":
                    out.days_holiday -= Decimal("1")
                elif was == "week_off":
                    out.days_weekoff -= Decimal("1")
                out.days_absent += Decimal("1")
                out.days_sandwich += Decimal("1")
                out.working_days += Decimal("1")
                out.by_date[d] = "absent_sandwich"

    return out

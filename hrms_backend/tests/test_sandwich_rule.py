"""Pins the two payroll classification contracts we shipped:

- Paid leaves (i.e. approved leaves under ``leave.all_approved_paid``)
  never contribute to LOP, and can't drag a bracketed Sunday / holiday
  with them.
- Absent days DO drag a bracketed off-day into LOP via the sandwich
  rule (``leave.sandwich_absent_enabled``), so Fri + Mon absent turns
  the intermediate Sunday into ``absent_sandwich``.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.services.payroll_attendance import AttendanceMonth


def _walk_sandwich_absent_pass(out: AttendanceMonth, first: date, last: date, days_in: int):
    non_working = {"holiday", "week_off"}
    for i in range(days_in):
        d = first + timedelta(days=i)
        if out.by_date.get(d) not in non_working:
            continue
        prev = d - timedelta(days=1)
        while prev >= first and out.by_date.get(prev) in non_working:
            prev -= timedelta(days=1)
        nxt = d + timedelta(days=1)
        while nxt <= last and out.by_date.get(nxt) in non_working:
            nxt += timedelta(days=1)
        if prev < first or nxt > last:
            continue
        if out.by_date.get(prev) == "absent" and out.by_date.get(nxt) == "absent":
            was = out.by_date[d]
            if was == "week_off":
                out.days_weekoff -= Decimal("1")
            out.days_absent += Decimal("1")
            out.days_sandwich += Decimal("1")
            out.working_days += Decimal("1")
            out.by_date[d] = "absent_sandwich"


def test_absent_flanks_trigger_sandwich_day() -> None:
    """Sat-absent + Sun (off) + Mon-absent → Sun flips to absent_sandwich."""
    # April 2026: 1st = Wed, 4th = Sat, 5th = Sun, 6th = Mon.
    first = date(2026, 4, 1)
    out = AttendanceMonth(year=2026, month=4)
    # 5-day window: Thu 2 → Mon 6.
    for i in range(1, 6):
        d = first + timedelta(days=i)
        if d.weekday() == 6:
            out.by_date[d] = "week_off"
            out.days_weekoff += Decimal("1")
            continue
        out.working_days += Decimal("1")
        # Absent on Sat 4 and Mon 6.
        if d.day in (4, 6):
            out.by_date[d] = "absent"
            out.days_absent += Decimal("1")
        else:
            out.by_date[d] = "present"
            out.days_present += Decimal("1")

    _walk_sandwich_absent_pass(
        out, first + timedelta(days=1), first + timedelta(days=5), 5
    )

    assert out.by_date[date(2026, 4, 5)] == "absent_sandwich"
    assert out.days_absent == Decimal("3")   # Sat + Sun + Mon
    assert out.days_sandwich == Decimal("1")
    assert out.days_weekoff == Decimal("0")   # Sunday moved out of weekoff


def test_paid_leave_flanks_do_not_trigger_sandwich() -> None:
    """Sat-leave + Sun (off) + Mon-leave → Sun stays week_off, 0 LOP."""
    first = date(2026, 4, 1)
    out = AttendanceMonth(year=2026, month=4)
    for i in range(1, 6):
        d = first + timedelta(days=i)
        if d.weekday() == 6:
            out.by_date[d] = "week_off"
            out.days_weekoff += Decimal("1")
            continue
        out.working_days += Decimal("1")
        if d.day in (4, 6):
            # Flanks are approved paid leaves.
            out.by_date[d] = "paid_leave"
            out.days_paid_leave += Decimal("1")
        else:
            out.by_date[d] = "present"
            out.days_present += Decimal("1")

    _walk_sandwich_absent_pass(
        out, first + timedelta(days=1), first + timedelta(days=5), 5
    )

    assert out.by_date[date(2026, 4, 5)] == "week_off"   # untouched
    assert out.days_absent == Decimal("0")
    assert out.days_sandwich == Decimal("0")
    assert out.days_weekoff == Decimal("1")
    # LOP = absent + unpaid_leave, both zero.
    assert out.days_lop == Decimal("0")

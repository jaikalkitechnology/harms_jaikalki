"""Seed shifts, leave types, holidays + bootstrap balances/default shifts.

Run after seed_employees.py:

    python -m scripts.seed_attendance_leave
"""
from __future__ import annotations

import asyncio
from datetime import date, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Employee,
    EmployeeShift,
    Holiday,
    LeaveBalance,
    LeaveType,
    Shift,
)


SHIFTS = [
    ("GEN", "General", time(9, 0), time(18, 0), 60, True),
    ("EARLY", "Early", time(6, 0), time(15, 0), 60, False),
    ("LATE", "Late", time(14, 0), time(23, 0), 60, False),
    ("NIGHT", "Night", time(22, 0), time(7, 0), 60, False),
]


# (code, name, days/year, carry_forward, max_cf, requires_attachment_after_days,
#  description, is_paid, applies_sandwich_rule)
# Leave year runs APRIL → MARCH (Indian financial year). Carry-forward
# is allowed for PL only.
LEAVE_TYPES = [
    ("CL", "Casual Leave", Decimal("6"), False, Decimal("0"), 0,
     "6 days per leave-year (Apr–Mar). No carry forward.", True, False),
    ("SL", "Sick Leave", Decimal("8"), False, Decimal("0"), 3,
     "8 days per leave-year. Doctor's note for 3+ consecutive days.",
     True, False),
    ("PL", "Privilege Leave", Decimal("18"), True, Decimal("18"), 0,
     "18 days per leave-year. Earned leave — carries forward (cap 18).",
     True, False),
    ("ML", "Maternity Leave", Decimal("180"), False, Decimal("0"), 0,
     "180 days as per the Maternity Benefit Act.", True, False),
    ("PTL", "Paternity Leave", Decimal("7"), False, Decimal("0"), 0,
     "7 days within 6 months of childbirth.", True, False),
    ("BL", "Bereavement Leave", Decimal("0"), False, Decimal("0"), 0,
     "Granted ad-hoc by HR; no standing allocation.", True, False),
    ("LWP", "Leave Without Pay", Decimal("0"), False, Decimal("0"), 0,
     "Unpaid leave. Sandwich rule applies — Sundays/holidays falling "
     "between two LWP days are also unpaid.", False, True),
]


HOLIDAYS_2026 = [
    (date(2026, 1, 1), "New Year's Day", "national"),
    (date(2026, 1, 26), "Republic Day", "national"),
    (date(2026, 3, 4), "Holi", "national"),
    (date(2026, 4, 14), "Ambedkar Jayanti", "national"),
    (date(2026, 5, 1), "Labour Day", "national"),
    (date(2026, 8, 15), "Independence Day", "national"),
    (date(2026, 10, 2), "Gandhi Jayanti", "national"),
    (date(2026, 11, 1), "Diwali", "national"),
]


async def seed_shifts(db: AsyncSession) -> dict[str, Shift]:
    existing = {
        s.code: s for s in (await db.execute(select(Shift))).scalars().all()
    }
    for code, name, start, end, brk, default in SHIFTS:
        if code not in existing:
            s = Shift(
                code=code,
                name=name,
                start_time=start,
                end_time=end,
                break_duration_min=brk,
                is_default=default,
                is_active=True,
            )
            db.add(s)
            existing[code] = s
    await db.flush()
    return existing


async def seed_leave_types(db: AsyncSession) -> dict[str, LeaveType]:
    existing = {
        t.code: t for t in (await db.execute(select(LeaveType))).scalars().all()
    }
    for code, name, days, cf, max_cf, attach_after, desc, is_paid, sandwich in LEAVE_TYPES:
        if code not in existing:
            t = LeaveType(
                code=code,
                name=name,
                days_per_year=days,
                carry_forward=cf,
                max_carry_forward=max_cf,
                encashable=False,
                requires_attachment_after_days=attach_after,
                description=desc,
                is_paid=is_paid,
                applies_sandwich_rule=sandwich,
                is_active=True,
            )
            db.add(t)
            existing[code] = t
        else:
            # Keep day counts / carry-forward / flags in sync when the
            # seed evolves (e.g. CL 12→6, FY April–March policy change).
            t = existing[code]
            t.name = name
            t.days_per_year = days
            t.carry_forward = cf
            t.max_carry_forward = max_cf
            t.requires_attachment_after_days = attach_after
            t.description = desc
            t.is_paid = is_paid
            t.applies_sandwich_rule = sandwich
            t.is_active = True
    await db.flush()
    return existing


async def seed_holidays(db: AsyncSession) -> None:
    existing = {
        (h.date, h.location)
        for h in (await db.execute(select(Holiday))).scalars().all()
    }
    for d, name, htype in HOLIDAYS_2026:
        if (d, "ALL") in existing:
            continue
        db.add(
            Holiday(date=d, name=name, type=htype, is_optional=False, location="ALL")
        )
    await db.flush()


async def bootstrap_employee_shifts_and_balances(
    db: AsyncSession,
    shifts: dict[str, Shift],
    leave_types: dict[str, LeaveType],
) -> None:
    today = date.today()
    year = today.year
    default_shift = shifts.get("GEN")
    employees = (
        await db.execute(select(Employee).where(Employee.status == "active"))
    ).scalars().all()

    existing_emp_shift = {
        es.employee_id
        for es in (await db.execute(select(EmployeeShift))).scalars().all()
    }
    existing_balances = {
        (b.employee_id, b.leave_type_id, b.year)
        for b in (await db.execute(select(LeaveBalance))).scalars().all()
    }

    for emp in employees:
        if default_shift and emp.id not in existing_emp_shift:
            db.add(
                EmployeeShift(
                    employee_id=emp.id,
                    shift_id=default_shift.id,
                    effective_from=emp.date_of_joining or today,
                )
            )
        # Skip salary-bearing leave for interns (no salary, no leave allocation).
        is_intern = emp.category and emp.category.code == "INTERN"
        for code, lt in leave_types.items():
            # Interns don't get any leave allocation.
            if is_intern:
                continue
            if (emp.id, lt.id, year) in existing_balances:
                continue
            db.add(
                LeaveBalance(
                    employee_id=emp.id,
                    leave_type_id=lt.id,
                    year=year,
                    allocated=lt.days_per_year,
                    used=Decimal("0"),
                    carried_forward=Decimal("0"),
                )
            )
    await db.flush()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        shifts = await seed_shifts(db)
        leave_types = await seed_leave_types(db)
        await seed_holidays(db)
        await bootstrap_employee_shifts_and_balances(db, shifts, leave_types)
        await db.commit()
    print("✔ Attendance & leave seed complete")
    print(f"  · {len(SHIFTS)} shifts")
    print(f"  · {len(LEAVE_TYPES)} leave types")
    print(f"  · {len(HOLIDAYS_2026)} holidays for 2026")


if __name__ == "__main__":
    asyncio.run(run())

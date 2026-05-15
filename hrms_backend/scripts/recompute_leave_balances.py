"""Recompute leave balances across financial years (Apr → Mar).

Run after the attendance import / leave-type seed:

    # Default: FY 2025 then FY 2026 (carry-forward chains 2025→2026)
    python3 -m scripts.recompute_leave_balances
    python3 -m scripts.recompute_leave_balances --from-fy 2025 --to-fy 2027
    python3 -m scripts.recompute_leave_balances --dry-run

Years in the range are processed in order, so unused PL from FY 2025
correctly carries into FY 2026, then FY 2026's leftover into FY 2027,
and so on.

For every active employee, for each FY <start>-04-01 → <start+1>-03-31:

1.  Ensures a LeaveBalance row per active leave type for that FY with
    `allocated` = the leave type's days_per_year (CL 6, SL 8, PL 18,
    ML 180, PTL 7, BL 0, LWP 0) and `used` reset to 0.
2.  PL carry-forward — **confirmed employees only**. Unused PL from the
    previous FY is carried into `carried_forward`, capped at
    PL.max_carry_forward. Employees still on probation do NOT carry PL
    across the boundary (they still get a fresh allocation). All
    non-PL leave types reset clean each FY.
3.  Replays consumption inside the window:
      • Approved LeaveRequests → days deducted from their own
        leave type (clipped to the FY window, half-days respected).
      • Attendance rows with status='leave' that are NOT already
        covered by an approved LeaveRequest are "unattributed". Those
        are charged to PL first; once PL (allocated + carried) is
        exhausted they cascade to CL, then SL; anything still left is
        reported as LWP (unpaid) and not charged to a paid bucket.

Idempotent — re-running fully rebuilds the range from source data, so
it's safe to run after every attendance correction.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Attendance,
    Employee,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)
from app.utils.leave_year import financial_year_range

# Order the unattributed-leave cascade follows: PL first, then CL, SL.
_CASCADE = ["PL", "CL", "SL"]


async def _balance(
    db: AsyncSession,
    *,
    employee_id: int,
    lt: LeaveType,
    fy: int,
) -> LeaveBalance:
    bal = (
        await db.execute(
            select(LeaveBalance)
            .where(LeaveBalance.employee_id == employee_id)
            .where(LeaveBalance.leave_type_id == lt.id)
            .where(LeaveBalance.year == fy)
        )
    ).scalar_one_or_none()
    if bal is None:
        bal = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=lt.id,
            year=fy,
            allocated=lt.days_per_year,
            used=Decimal("0"),
            carried_forward=Decimal("0"),
        )
        db.add(bal)
        await db.flush()
    return bal


async def _recompute_one_fy(
    db: AsyncSession,
    *,
    fy: int,
    by_code: dict[str, LeaveType],
    pl: LeaveType,
    employees: list[Employee],
) -> None:
    first, last = financial_year_range(fy)
    print(f"  ── FY {fy} ({first} → {last}) ──")

    for emp in employees:
        # 1. (Re)allocate every leave type for this FY, reset used.
        balances: dict[str, LeaveBalance] = {}
        for code, lt in by_code.items():
            bal = await _balance(db, employee_id=emp.id, lt=lt, fy=fy)
            bal.allocated = lt.days_per_year
            bal.used = Decimal("0")
            bal.carried_forward = Decimal("0")
            balances[code] = bal

        # 2. PL carry-forward from the previous FY — CONFIRMED
        #    employees only. Anyone still on probation forfeits the
        #    carry-forward (they accrue a fresh allocation but don't
        #    bank unused PL across the probation boundary).
        is_confirmed = not bool(emp.is_on_probation)
        if is_confirmed:
            prev_pl = (
                await db.execute(
                    select(LeaveBalance)
                    .where(LeaveBalance.employee_id == emp.id)
                    .where(LeaveBalance.leave_type_id == pl.id)
                    .where(LeaveBalance.year == fy - 1)
                )
            ).scalar_one_or_none()
            if prev_pl is not None:
                prev_remaining = (
                    (prev_pl.allocated or Decimal("0"))
                    + (prev_pl.carried_forward or Decimal("0"))
                    - (prev_pl.used or Decimal("0"))
                )
                cap = pl.max_carry_forward or Decimal("0")
                cf = max(Decimal("0"), min(prev_remaining, cap))
                balances["PL"].carried_forward = cf

        # 3a. Approved leave requests overlapping the FY window.
        leave_reqs = (
            await db.execute(
                select(LeaveRequest)
                .where(LeaveRequest.employee_id == emp.id)
                .where(LeaveRequest.status == "approved")
                .where(LeaveRequest.from_date <= last)
                .where(LeaveRequest.to_date >= first)
            )
        ).scalars().all()

        covered: set[date] = set()
        for lr in leave_reqs:
            lt = lr.leave_type
            code = lt.code if lt else None
            d = max(lr.from_date, first)
            end = min(lr.to_date, last)
            day_count = 0
            while d <= end:
                covered.add(d)
                day_count += 1
                d += timedelta(days=1)
            if not day_count or code not in balances:
                continue
            charge = (
                lr.days
                if lr.half_day and lr.days
                else Decimal(day_count)
            )
            balances[code].used += Decimal(charge)

        # 3b. Unattributed attendance 'leave' days → cascade PL→CL→SL.
        att_leaves = (
            await db.execute(
                select(Attendance)
                .where(Attendance.employee_id == emp.id)
                .where(Attendance.status == "leave")
                .where(Attendance.date >= first)
                .where(Attendance.date <= last)
            )
        ).scalars().all()

        unattributed = sorted(
            a.date for a in att_leaves if a.date not in covered
        )
        lwp_days = 0
        for _day in unattributed:
            placed = False
            for code in _CASCADE:
                bal = balances.get(code)
                if bal is None:
                    continue
                avail = (
                    (bal.allocated or Decimal("0"))
                    + (bal.carried_forward or Decimal("0"))
                    - (bal.used or Decimal("0"))
                )
                if avail >= Decimal("1"):
                    bal.used += Decimal("1")
                    placed = True
                    break
            if not placed:
                lwp_days += 1
                if "LWP" in balances:
                    balances["LWP"].used += Decimal("1")

        taken = {
            c: str(b.used)
            for c, b in balances.items()
            if (b.used or 0) and float(b.used) > 0
        }
        if taken or balances["PL"].carried_forward:
            tag = "" if is_confirmed else " (probation — no PL c/f)"
            print(
                f"    {emp.employee_code:8s} {emp.first_name} {emp.last_name}: "
                f"PL c/f={balances['PL'].carried_forward} "
                f"used={taken or '—'}"
                + (f" LWP={lwp_days}" if lwp_days else "")
                + tag
            )

    # Flush so the next FY in the range can read these PL balances
    # for its carry-forward step.
    await db.flush()


async def main(*, from_fy: int, to_fy: int, dry_run: bool) -> None:
    if to_fy < from_fy:
        print("!! --to-fy must be >= --from-fy", file=sys.stderr)
        sys.exit(2)
    print(
        f"→ Recomputing leave balances FY {from_fy} … FY {to_fy} "
        f"(carry-forward chains forward year by year)"
    )

    async with AsyncSessionLocal() as db:
        types = (await db.execute(select(LeaveType))).scalars().all()
        by_code = {t.code: t for t in types}
        pl = by_code.get("PL")
        if pl is None:
            print("!! PL leave type missing — run seed_attendance_leave first.",
                  file=sys.stderr)
            sys.exit(2)

        employees = (
            await db.execute(
                select(Employee).where(Employee.status == "active")
            )
        ).scalars().all()
        print(f"  {len(employees)} active employees, {len(types)} leave types.")

        for fy in range(from_fy, to_fy + 1):
            await _recompute_one_fy(
                db, fy=fy, by_code=by_code, pl=pl, employees=employees
            )

        if dry_run:
            print("→ Dry run; rolling back.")
            await db.rollback()
        else:
            await db.commit()
            print("→ Committed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-fy",
        type=int,
        default=2025,
        help="First financial-year start year (default 2025 = Apr'25–Mar'26).",
    )
    parser.add_argument(
        "--to-fy",
        type=int,
        default=2026,
        help="Last financial-year start year (default 2026 = Apr'26–Mar'27). "
        "Years are processed in order so PL carry-forward chains.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without committing.",
    )
    args = parser.parse_args()
    asyncio.run(
        main(from_fy=args.from_fy, to_fy=args.to_fy, dry_run=args.dry_run)
    )

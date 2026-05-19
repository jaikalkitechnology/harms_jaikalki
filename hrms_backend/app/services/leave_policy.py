"""Leave policy — sandwich rule + earned-leave accrual.

Settings live in the SystemConfig table (keys prefixed `leave.`) so they
can be edited from the admin Settings page without redeploys.
Recomputation is idempotent — running it daily, weekly, or on every
leave application all converge on the same number."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Attendance,
    EarnedLeaveAccrual,
    Employee,
    LeaveBalance,
    LeaveType,
    SystemConfig,
    User,
)


_DEFAULTS: dict[str, object] = {
    # When True, intermediate Sundays/holidays inside a leave range that
    # is bracketed by working-day leaves count toward the leave total.
    "leave.sandwich_enabled": False,
    # Whether public holidays inside the leave range are also counted
    # under the sandwich rule (Sundays always are when enabled).
    "leave.sandwich_count_holidays": True,
    # Earned-leave accrual: 1 PL earned per 20 qualifying days. A
    # qualifying day = any calendar day that is NOT leave and NOT
    # absent — so present / WFH / half-day AND Sundays / holidays all
    # count. Auto-enabled (no flat PL allocation any more).
    "leave.earned_accrual_enabled": True,
    "leave.earned_accrual_days_required": 20,
    "leave.earned_accrual_credit_days": 1,
    "leave.earned_accrual_leave_type_code": "PL",
}

_KEYS = list(_DEFAULTS.keys())


async def get_leave_policy(db: AsyncSession) -> dict:
    rows = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
        )
    ).scalars().all()
    cfg = {r.key: r.value for r in rows}
    out: dict = {}
    for k, v in _DEFAULTS.items():
        out[k.removeprefix("leave.")] = (
            cfg[k] if k in cfg and cfg[k] is not None else v
        )
    return out


async def set_leave_policy(
    db: AsyncSession,
    payload: dict,
    *,
    actor: Optional[User] = None,
) -> dict:
    """Upsert any keys that differ from defaults. Unknown keys are ignored."""
    existing = {
        r.key: r
        for r in (
            await db.execute(
                select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
            )
        ).scalars().all()
    }
    for short_key, default in _DEFAULTS.items():
        bare = short_key.removeprefix("leave.")
        if bare not in payload:
            continue
        v = _coerce(payload[bare], default)
        row = existing.get(short_key)
        if row:
            row.value = v
            if actor:
                row.updated_by = actor.id
        else:
            db.add(
                SystemConfig(
                    key=short_key,
                    value=v,
                    category="leave",
                    description=f"Leave policy: {short_key}",
                    is_secret=False,
                    updated_by=actor.id if actor else None,
                )
            )
    await db.commit()
    return await get_leave_policy(db)


def _coerce(value: object, like: object) -> object:
    """Best-effort cast incoming value to the type of the default."""
    if isinstance(like, bool):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)
    if isinstance(like, int) and not isinstance(like, bool):
        return int(value)
    if isinstance(like, (Decimal, float)):
        return float(value)
    return value


# ── Sandwich rule ─────────────────────────────────────────────────────
def count_leave_days(
    from_date: date,
    to_date: date,
    holidays: set[date],
    *,
    sandwich_enabled: bool,
    sandwich_count_holidays: bool = True,
) -> Decimal:
    """Count leave days for a request.

    Standard mode: skip Sundays + holidays.

    Sandwich mode: when both endpoints are working days (not Sun/holiday),
    intermediate Sundays — and optionally intermediate holidays — count.
    A 1-day leave on a Saturday is unaffected; a leave from Sat to Mon
    becomes 3 days instead of 2."""
    if from_date > to_date:
        return Decimal("0")

    def _is_off(d: date) -> bool:
        return d.weekday() == 6 or d in holidays

    if not sandwich_enabled:
        days = 0
        d = from_date
        while d <= to_date:
            if not _is_off(d):
                days += 1
            d = d + timedelta(days=1)
        return Decimal(days)

    # Sandwich: only apply if BOTH endpoints are working days.
    if _is_off(from_date) or _is_off(to_date):
        # endpoint is itself an off-day → fall back to standard count
        return count_leave_days(
            from_date, to_date, holidays,
            sandwich_enabled=False,
        )

    days = 0
    d = from_date
    while d <= to_date:
        if d.weekday() == 6:
            days += 1  # Sunday counts under sandwich
        elif d in holidays:
            days += 1 if sandwich_count_holidays else 0
        else:
            days += 1
        d = d + timedelta(days=1)
    return Decimal(days)


# ── Earned-leave accrual ──────────────────────────────────────────────
def _today() -> date:
    return datetime.utcnow().date()


PRESENT_STATUSES = ("present", "wfh", "half_day")


async def recompute_earned_leaves(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
) -> dict:
    """Idempotent: for every active employee (or just one), recompute
    `days_credited = floor(present_count / threshold) * credit_per` and
    sync the matching LeaveBalance row.

    Returns a summary dict {policy, processed, credited_total}."""
    policy = await get_leave_policy(db)
    if not policy["earned_accrual_enabled"]:
        return {"enabled": False, "processed": 0, "credited_total": 0}

    threshold = max(1, int(policy["earned_accrual_days_required"]))
    credit_per = Decimal(str(policy["earned_accrual_credit_days"]))
    type_code = str(policy["earned_accrual_leave_type_code"]).upper()

    leave_type = (
        await db.execute(select(LeaveType).where(LeaveType.code == type_code))
    ).scalar_one_or_none()
    if not leave_type:
        return {
            "enabled": True,
            "processed": 0,
            "credited_total": 0,
            "error": f"leave type '{type_code}' not found",
        }

    # Accrual runs on the Apr–Mar financial year, same as the rest of
    # the leave system. `year` is the FY start year; the qualifying
    # window is 1 Apr of that FY → today.
    from app.utils.leave_year import (
        financial_year_range,
        financial_year_start,
    )

    today = _today()
    year = financial_year_start(today)
    win_start, _fy_end = financial_year_range(year)
    elapsed = (today - win_start).days + 1
    emp_stmt = select(Employee).where(Employee.status == "active")
    if employee_id is not None:
        emp_stmt = emp_stmt.where(Employee.id == employee_id)
    employees = (await db.execute(emp_stmt)).scalars().all()

    total = Decimal("0")
    processed = 0
    for emp in employees:
        # Qualifying day = a calendar day from Jan 1 → today that is
        # NOT a recorded leave and NOT a recorded absent. Present /
        # WFH / half-day plus Sundays & holidays all qualify (they're
        # part of `elapsed` and aren't leave/absent rows).
        leave_days = (
            await db.execute(
                select(func.count(Attendance.id))
                .where(Attendance.employee_id == emp.id)
                .where(Attendance.status == "leave")
                .where(Attendance.date >= win_start)
                .where(Attendance.date <= today)
            )
        ).scalar() or 0
        absent_days = (
            await db.execute(
                select(func.count(Attendance.id))
                .where(Attendance.employee_id == emp.id)
                .where(Attendance.status == "absent")
                .where(Attendance.date >= win_start)
                .where(Attendance.date <= today)
            )
        ).scalar() or 0
        qualifying = max(0, elapsed - int(leave_days) - int(absent_days))

        # Idempotent target — 1 PL per `threshold` qualifying days.
        target = (Decimal(qualifying) // Decimal(threshold)) * credit_per

        ledger = (
            await db.execute(
                select(EarnedLeaveAccrual)
                .where(EarnedLeaveAccrual.employee_id == emp.id)
                .where(EarnedLeaveAccrual.leave_type_id == leave_type.id)
                .where(EarnedLeaveAccrual.year == year)
            )
        ).scalar_one_or_none()

        delta = target - (ledger.days_credited if ledger else Decimal("0"))

        if ledger is None:
            ledger = EarnedLeaveAccrual(
                employee_id=emp.id,
                leave_type_id=leave_type.id,
                year=year,
                days_credited=target,
                last_present_count=int(present_count),
                last_recomputed_at=datetime.utcnow(),
            )
            db.add(ledger)
        else:
            ledger.days_credited = target
            ledger.last_present_count = int(present_count)
            ledger.last_recomputed_at = datetime.utcnow()

        # Sync the balance. Accrual owns `allocated` for this leave
        # type (PL has no flat days_per_year any more), leaving
        # carried_forward = prior-FY carry and adjustment = manual HR
        # corrections untouched. balance = allocated + carried_forward
        # + adjustment − used.
        bal = (
            await db.execute(
                select(LeaveBalance)
                .where(LeaveBalance.employee_id == emp.id)
                .where(LeaveBalance.leave_type_id == leave_type.id)
                .where(LeaveBalance.year == year)
            )
        ).scalar_one_or_none()
        if bal is None:
            bal = LeaveBalance(
                employee_id=emp.id,
                leave_type_id=leave_type.id,
                year=year,
                allocated=target,
                used=Decimal("0"),
                carried_forward=Decimal("0"),
            )
            db.add(bal)
        else:
            bal.allocated = target

        total += delta if delta > 0 else Decimal("0")
        processed += 1

    await db.commit()
    return {
        "enabled": True,
        "processed": processed,
        "credited_total": float(total),
        "policy": policy,
    }

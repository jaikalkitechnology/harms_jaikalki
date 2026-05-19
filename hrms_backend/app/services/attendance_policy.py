"""Attendance policy — late-grace rule + future shift overrides.

Settings live in the SystemConfig table (keys prefixed `attendance.`)
so HR / super-admin can edit them from the admin Settings page."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, time
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Attendance,
    Employee,
    EmployeeShift,
    Shift,
    SystemConfig,
    User,
)


_DEFAULTS: dict[str, object] = {
    # Legacy single-threshold half-day rule (kept for back-compat).
    # 0 disables it; the richer rule below is preferred.
    "attendance.late_grace_minutes": 0,
    # Default shift start when an employee has no assigned shift.
    # HH:MM string; parsed at runtime.
    "attendance.default_shift_start": "09:00",
    # Minutes past shift start after which a check-in is flagged
    # `is_late` (records a remark; day stays full unless the half-day
    # rule below also fires).
    "attendance.late_mark_minutes": 10,
    # Minutes past shift start that count as a "very late" occurrence
    # (candidate for half-day).
    "attendance.halfday_after_minutes": 60,
    # Very-late occurrences per month cycle that are forgiven (full
    # day). From the (N+1)th onward the day is auto half_day.
    # e.g. 2 ⇒ 1st & 2nd very-late are full, 3rd+ half.
    "attendance.halfday_free_count": 2,
}

_KEYS = list(_DEFAULTS.keys())


async def get_attendance_policy(db: AsyncSession) -> dict:
    rows = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
        )
    ).scalars().all()
    cfg = {r.key: r.value for r in rows}
    out: dict = {}
    for k, v in _DEFAULTS.items():
        out[k.removeprefix("attendance.")] = (
            cfg[k] if k in cfg and cfg[k] is not None else v
        )
    return out


async def set_attendance_policy(
    db: AsyncSession,
    payload: dict,
    *,
    actor: Optional[User] = None,
) -> dict:
    existing = {
        r.key: r
        for r in (
            await db.execute(
                select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
            )
        ).scalars().all()
    }
    for full_key, default in _DEFAULTS.items():
        bare = full_key.removeprefix("attendance.")
        if bare not in payload:
            continue
        v = payload[bare]
        if isinstance(default, int):
            v = int(v)
        elif isinstance(default, str):
            v = str(v)
        row = existing.get(full_key)
        if row:
            row.value = v
            if actor:
                row.updated_by = actor.id
        else:
            db.add(
                SystemConfig(
                    key=full_key,
                    value=v,
                    category="attendance",
                    description=f"Attendance policy: {full_key}",
                    is_secret=False,
                    updated_by=actor.id if actor else None,
                )
            )
    await db.commit()
    return await get_attendance_policy(db)


# ── Late-grace evaluator (called from check_in) ───────────────────────
async def shift_start_for_employee(
    db: AsyncSession, employee_id: int
) -> time:
    """Resolve the start time of the employee's currently assigned shift.
    Falls back to the configured default (09:00) if none."""
    row = (
        await db.execute(
            select(Shift)
            .join(EmployeeShift, EmployeeShift.shift_id == Shift.id)
            .where(EmployeeShift.employee_id == employee_id)
            .where(EmployeeShift.effective_to.is_(None))
            .order_by(EmployeeShift.effective_from.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row:
        return row.start_time

    policy = await get_attendance_policy(db)
    raw = str(policy.get("default_shift_start", "09:00"))
    try:
        h, m = raw.split(":")[:2]
        return time(int(h), int(m))
    except Exception:
        return time(9, 0)


def is_late(check_in_time: time, shift_start: time, grace_minutes: int) -> bool:
    """Return True if check-in is more than `grace_minutes` past the
    shift start. grace_minutes <= 0 disables the rule."""
    if grace_minutes <= 0:
        return False
    cm = check_in_time.hour * 60 + check_in_time.minute
    sm = shift_start.hour * 60 + shift_start.minute
    return (cm - sm) > grace_minutes


# Tag written into late_remark for ">1h late" days so prior
# occurrences in the cycle can be counted deterministically.
_VL_TAG = "[VL]"


async def _cycle_window(db: AsyncSession, employee_id: int, on: date):
    """(first, last) of the month cycle containing `on`, honouring the
    employee's attendance_cycle_start_day (1 = calendar month)."""
    emp = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    start_day = max(1, int(getattr(emp, "attendance_cycle_start_day", 1) or 1))
    if start_day == 1:
        first = on.replace(day=1)
        last = on.replace(day=monthrange(on.year, on.month)[1])
        return first, last
    # Cycle N → the window is N-of-prev-month .. (N-1)-of-this-month.
    if on.day >= start_day:
        first = on.replace(day=min(start_day, monthrange(on.year, on.month)[1]))
        nx_y = on.year + (1 if on.month == 12 else 0)
        nx_m = 1 if on.month == 12 else on.month + 1
        last = date(nx_y, nx_m, min(start_day - 1, monthrange(nx_y, nx_m)[1]))
    else:
        pv_y = on.year - (1 if on.month == 1 else 0)
        pv_m = 12 if on.month == 1 else on.month - 1
        first = date(pv_y, pv_m, min(start_day, monthrange(pv_y, pv_m)[1]))
        last = on.replace(day=min(start_day - 1, monthrange(on.year, on.month)[1]))
    return first, last


async def apply_late_rule(
    db: AsyncSession, attendance: Attendance, employee_id: int
) -> None:
    """Shift-based late / half-day rule.

    • > late_mark_minutes past shift start  → flag is_late + remark.
    • > halfday_after_minutes               → a "very late" occurrence.
        The first `halfday_free_count` very-late days per month cycle
        stay full; from the next one onward the day is half_day.

    The legacy single-threshold late_grace rule still applies if set.
    No-op when the row isn't a working-present row.
    """
    if attendance.status not in ("present", "wfh"):
        return
    if not attendance.check_in:
        return

    policy = await get_attendance_policy(db)
    shift_start = await shift_start_for_employee(db, employee_id)
    ci = attendance.check_in.time()
    minutes_late = (ci.hour * 60 + ci.minute) - (
        shift_start.hour * 60 + shift_start.minute
    )
    on = attendance.date

    late_mark = int(policy.get("late_mark_minutes") or 0)
    halfday_after = int(policy.get("halfday_after_minutes") or 0)
    free_count = int(policy.get("halfday_free_count") or 0)

    def _note(msg: str) -> None:
        existing = (attendance.notes or "").rstrip()
        attendance.notes = (existing + " · " + msg) if existing else msg

    # 1. Flag late.
    if late_mark > 0 and minutes_late > late_mark:
        attendance.is_late = True
        very_late = halfday_after > 0 and minutes_late > halfday_after
        base = (
            f"Late by {minutes_late}m "
            f"(shift {shift_start.strftime('%H:%M')})"
        )
        attendance.late_remark = (
            f"{_VL_TAG} {base}" if very_late else base
        )

        # 2. Half-day escalation for repeat very-late days in the cycle.
        if very_late and free_count >= 0:
            first, last = await _cycle_window(db, employee_id, on)
            prior_vl = (
                await db.execute(
                    select(func.count(Attendance.id))
                    .where(Attendance.employee_id == employee_id)
                    .where(Attendance.date >= first)
                    .where(Attendance.date < on)
                    .where(Attendance.is_late.is_(True))
                    .where(Attendance.late_remark.like(f"{_VL_TAG}%"))
                )
            ).scalar() or 0
            occurrence = int(prior_vl) + 1  # including today
            if occurrence > free_count:
                attendance.status = "half_day"
                _note(
                    f"Auto half-day: very-late occurrence "
                    f"#{occurrence} this cycle (>{halfday_after}m, "
                    f"first {free_count} forgiven)."
                )
            else:
                _note(
                    f"Very late (#{occurrence}/{free_count} forgiven "
                    f"this cycle) — full day."
                )

    # 3. Legacy single-threshold rule (only if explicitly configured).
    grace = int(policy.get("late_grace_minutes") or 0)
    if (
        grace > 0
        and attendance.status in ("present", "wfh")
        and minutes_late > grace
    ):
        attendance.status = "half_day"
        _note(
            f"Auto half-day: late by >{grace}m "
            f"(shift {shift_start.strftime('%H:%M')})."
        )

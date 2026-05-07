"""Attendance policy — late-grace rule + future shift overrides.

Settings live in the SystemConfig table (keys prefixed `attendance.`)
so HR / super-admin can edit them from the admin Settings page."""
from __future__ import annotations

from datetime import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Attendance,
    EmployeeShift,
    Shift,
    SystemConfig,
    User,
)


_DEFAULTS: dict[str, object] = {
    # Threshold beyond shift start (in minutes) after which a check-in
    # is auto-marked as half_day. 0 disables the rule.
    "attendance.late_grace_minutes": 0,
    # Default shift start when an employee has no assigned shift.
    # HH:MM string; parsed at runtime.
    "attendance.default_shift_start": "09:00",
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


async def apply_late_rule(
    db: AsyncSession, attendance: Attendance, employee_id: int
) -> None:
    """Mutate the attendance row's status to half_day if check-in is
    past the configured grace window. No-op if the rule is disabled
    or the row is already non-present."""
    if attendance.status not in ("present", "wfh"):
        return
    if not attendance.check_in:
        return
    policy = await get_attendance_policy(db)
    grace = int(policy.get("late_grace_minutes") or 0)
    if grace <= 0:
        return
    shift_start = await shift_start_for_employee(db, employee_id)
    if is_late(attendance.check_in.time(), shift_start, grace):
        attendance.status = "half_day"
        existing_notes = (attendance.notes or "").rstrip()
        marker = (
            f"Auto-marked half day: late by >{grace}m "
            f"(shift start {shift_start.strftime('%H:%M')})."
        )
        attendance.notes = (
            (existing_notes + " · " + marker) if existing_notes else marker
        )

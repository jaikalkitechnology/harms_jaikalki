"""Payroll policy — division basis + related knobs.

Backed by the same ``SystemConfig`` table used by ``leave_policy`` so
admins can flip it from the Settings page without a redeploy. Keys are
prefixed ``payroll.``.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SystemConfig, User


_DEFAULTS: dict[str, object] = {
    # How to compute the payslip divisor.
    #   "calendar_days" (default) — divisor is the calendar days of the
    #     month being paid (30 for Sept, 31 for Oct, 28/29 for Feb).
    #     Payslip reads "Days Paid X / 30".
    #   "working_days" — divisor is the cycle window's working days
    #     (Sundays + holidays excluded). Legacy behaviour.
    #   "fixed_30" — divisor is always 30 regardless of month.
    "payroll.division_basis": "calendar_days",
}

_KEYS = list(_DEFAULTS.keys())


async def get_payroll_policy(db: AsyncSession) -> dict:
    rows = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
        )
    ).scalars().all()
    cfg = {r.key: r.value for r in rows}
    out: dict = {}
    for k, v in _DEFAULTS.items():
        out[k.removeprefix("payroll.")] = (
            cfg[k] if k in cfg and cfg[k] is not None else v
        )
    return out


async def set_payroll_policy(
    db: AsyncSession,
    payload: dict,
    *,
    actor: Optional[User] = None,
) -> dict:
    """Upsert payroll.* keys. Unknown keys are ignored."""
    existing = {
        r.key: r
        for r in (
            await db.execute(
                select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
            )
        ).scalars().all()
    }
    for full_key, default in _DEFAULTS.items():
        short = full_key.removeprefix("payroll.")
        if short not in payload:
            continue
        v = payload[short]
        # Basis is a whitelist of 3 strings.
        if short == "division_basis" and v not in (
            "calendar_days", "working_days", "fixed_30",
        ):
            continue
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
                    category="payroll",
                    description=f"Payroll policy: {full_key}",
                    is_secret=False,
                    updated_by=actor.id if actor else None,
                )
            )
    await db.commit()
    return await get_payroll_policy(db)

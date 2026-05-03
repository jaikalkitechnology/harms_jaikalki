"""Dynamic office geo-fence — backed by the SystemConfig table so super
admins / HR can change it from the UI without redeploying.

Falls back to the static settings.OFFICE_* values when no rows have been
stored yet (fresh installs, dev environments)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import SystemConfig, User

_KEYS = ("office.lat", "office.lng", "office.radius_m")


async def get_office_location(db: AsyncSession) -> tuple[float, float, int]:
    """Return (lat, lng, radius_m). Reads SystemConfig; falls back to
    config defaults when keys are unset."""
    rows = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
        )
    ).scalars().all()
    cfg = {r.key: r.value for r in rows}
    return (
        float(cfg.get("office.lat") or settings.OFFICE_LAT),
        float(cfg.get("office.lng") or settings.OFFICE_LNG),
        int(cfg.get("office.radius_m") or settings.OFFICE_RADIUS_M),
    )


async def set_office_location(
    db: AsyncSession,
    *,
    lat: float,
    lng: float,
    radius_m: int,
    actor: Optional[User] = None,
) -> tuple[float, float, int]:
    """Upsert the three SystemConfig keys."""
    payload = {
        "office.lat": lat,
        "office.lng": lng,
        "office.radius_m": radius_m,
    }
    existing = {
        r.key: r
        for r in (
            await db.execute(
                select(SystemConfig).where(SystemConfig.key.in_(_KEYS))
            )
        ).scalars().all()
    }
    for key, value in payload.items():
        row = existing.get(key)
        if row:
            row.value = value
            if actor:
                row.updated_by = actor.id
        else:
            db.add(
                SystemConfig(
                    key=key,
                    value=value,
                    category="office",
                    description=f"Office geo-fence: {key}",
                    is_secret=False,
                    updated_by=actor.id if actor else None,
                )
            )
    await db.commit()
    return await get_office_location(db)

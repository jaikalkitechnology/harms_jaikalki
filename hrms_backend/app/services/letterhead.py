"""Letterhead settings — the header / footer printed on every generated
letter (company name, CIN, GST, contact line, offices, footer note and
logo).

Stored as one JSON value in ``SystemConfig`` under ``letterhead`` so HR
can change it from Settings without a redeploy. Anything not set falls
back to the official Jaikalki letterhead text.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SystemConfig, User

KEY = "letterhead"

DEFAULTS: dict = {
    "company_name": "JAIKALKI TECHNOLOGY PRIVATE LIMITED",
    "cin": "U62091MH2025PTC438336",
    "gst": "27AAGCJ7035F1ZK",
    "phone": "+91 9136914963",
    "email": "info@jaikalki.com",
    "website": "www.jaikalki.com",
    "regd_office": (
        "Sh N B-2, First Floor, Mahavir Nagar, Deepak Hospital Road Lane, "
        "Mira Road East, Thane, Maharashtra, India, 401107."
    ),
    "corporate_office": (
        "Corporate Office:\n"
        "Sh N B-2, First Floor, Anand India Business Hub,\n"
        "Behind Shree Mahalaxmi Hospital,\n"
        "Deepak Hospital Road,\n"
        "Mira Road East,\n"
        "Thane – 401107."
    ),
    "footer_note": "",
    "show_watermark": True,
    "show_corner_accents": True,
    # Storage key of an uploaded logo; None = bundled Jaikalki logo.
    "logo_key": None,
}

# Plain-text fields HR can edit, with their length limits.
TEXT_FIELDS: dict[str, int] = {
    "company_name": 120,
    "cin": 40,
    "gst": 40,
    "phone": 60,
    "email": 120,
    "website": 120,
    "regd_office": 300,
    "corporate_office": 400,
    "footer_note": 160,
}
BOOL_FIELDS = ("show_watermark", "show_corner_accents")


def merge(stored: Optional[dict]) -> dict:
    out = dict(DEFAULTS)
    for k, v in (stored or {}).items():
        if k in DEFAULTS and v is not None:
            out[k] = v
    return out


def clean(payload: dict) -> dict:
    """Keep known fields only, trimmed to their limits."""
    out: dict = {}
    for k, limit in TEXT_FIELDS.items():
        if k in payload and payload[k] is not None:
            out[k] = str(payload[k]).strip()[:limit]
    for k in BOOL_FIELDS:
        if k in payload and payload[k] is not None:
            out[k] = bool(payload[k])
    return out


async def _row(db: AsyncSession) -> Optional[SystemConfig]:
    return (
        await db.execute(select(SystemConfig).where(SystemConfig.key == KEY))
    ).scalar_one_or_none()


async def get_letterhead(db: AsyncSession) -> dict:
    row = await _row(db)
    return merge(row.value if row and isinstance(row.value, dict) else None)


async def set_letterhead(
    db: AsyncSession, changes: dict, *, actor: Optional[User] = None
) -> dict:
    """Upsert. ``changes`` may also carry ``logo_key`` (set by the logo
    upload / reset endpoints)."""
    row = await _row(db)
    current = dict(row.value) if row and isinstance(row.value, dict) else {}
    current.update(changes)
    if row:
        # Re-assign so the JSON column is flagged dirty.
        row.value = current
        if actor:
            row.updated_by = actor.id
    else:
        db.add(
            SystemConfig(
                key=KEY,
                value=current,
                category="documents",
                description="Letterhead printed on generated letters",
                updated_by=actor.id if actor else None,
            )
        )
    await db.commit()
    return merge(current)

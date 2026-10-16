"""Polish features: assets, visitors, meeting rooms, internal job postings."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Asset,
    AssetAssignment,
    AssetCategory,
    Employee,
    JobApplication,
    JobPosting,
    MeetingRoom,
    RoomBooking,
    User,
    Visitor,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ─── Assets ──────────────────────────────────────────────────────────
ASSET_CONDITIONS = ("working", "damaged", "not_working", "expired")
RETURN_CONDITIONS = ASSET_CONDITIONS + ("lost",)

# Seeded on first use; HR can rename, add and disable them.
DEFAULT_CATEGORIES: list[dict] = [
    {"code": "laptop", "name": "Laptop", "spec_fields": [
        {"key": "processor", "label": "Processor"},
        {"key": "ram", "label": "RAM"},
        {"key": "storage", "label": "Storage"},
        {"key": "os", "label": "Operating system"},
    ]},
    {"code": "laptop_charger", "name": "Laptop charger", "is_accessory": True,
     "spec_fields": [{"key": "wattage", "label": "Wattage"}]},
    {"code": "mobile", "name": "Mobile phone", "spec_fields": [
        {"key": "imei", "label": "IMEI"},
        {"key": "ram", "label": "RAM"},
        {"key": "storage", "label": "Storage"},
    ]},
    {"code": "mobile_charger", "name": "Mobile charger", "is_accessory": True,
     "spec_fields": [{"key": "wattage", "label": "Wattage"}]},
    {"code": "sim_card", "name": "SIM card", "spec_fields": [
        {"key": "phone_number", "label": "Phone number"},
        {"key": "operator", "label": "Operator"},
    ]},
    {"code": "mouse", "name": "Mouse", "is_accessory": True},
    {"code": "keyboard", "name": "Keyboard", "is_accessory": True},
    {"code": "headset", "name": "Headset"},
    {"code": "monitor", "name": "Monitor", "spec_fields": [
        {"key": "screen_size", "label": "Screen size"},
        {"key": "resolution", "label": "Resolution"},
    ]},
    {"code": "vehicle", "name": "Vehicle", "spec_fields": [
        {"key": "registration_no", "label": "Registration no."},
    ]},
    {"code": "other", "name": "Other"},
]


async def ensure_default_categories(db: AsyncSession) -> None:
    """Seed the category list the first time it's needed."""
    if (await db.execute(select(AssetCategory.id).limit(1))).first():
        return
    for i, c in enumerate(DEFAULT_CATEGORIES):
        db.add(
            AssetCategory(
                code=c["code"],
                name=c["name"],
                is_accessory=c.get("is_accessory", False),
                spec_fields=c.get("spec_fields") or [],
                sort_order=(i + 1) * 10,
            )
        )
    await db.commit()


async def list_categories(
    db: AsyncSession, *, include_inactive: bool = False
) -> Sequence[AssetCategory]:
    await ensure_default_categories(db)
    stmt = select(AssetCategory).order_by(
        AssetCategory.sort_order, AssetCategory.name
    )
    if not include_inactive:
        stmt = stmt.where(AssetCategory.is_active.is_(True))
    return (await db.execute(stmt)).scalars().all()


def _slug(text: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")[:48]


def _clean_spec_fields(fields: Optional[list]) -> list[dict]:
    out, seen = [], set()
    for f in fields or []:
        label = str((f or {}).get("label") or "").strip()
        key = _slug(str((f or {}).get("key") or label))
        if label and key and key not in seen:
            seen.add(key)
            out.append({"key": key, "label": label[:60]})
    return out


async def create_category(db: AsyncSession, *, payload: dict) -> AssetCategory:
    await ensure_default_categories(db)
    code = _slug(payload.get("code") or payload["name"])
    if not code:
        raise ValidationError("Category name is required")
    if (
        await db.execute(select(AssetCategory).where(AssetCategory.code == code))
    ).scalar_one_or_none():
        raise ConflictError(f"A category with code '{code}' already exists")
    cat = AssetCategory(
        code=code,
        name=payload["name"].strip(),
        is_accessory=bool(payload.get("is_accessory")),
        spec_fields=_clean_spec_fields(payload.get("spec_fields")),
        sort_order=payload.get("sort_order") or 500,
        is_active=True,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def update_category(
    db: AsyncSession, category_id: int, *, payload: dict
) -> AssetCategory:
    cat = (
        await db.execute(select(AssetCategory).where(AssetCategory.id == category_id))
    ).scalar_one_or_none()
    if not cat:
        raise NotFoundError("Category not found")
    if "name" in payload and payload["name"]:
        cat.name = payload["name"].strip()
    if "is_accessory" in payload and payload["is_accessory"] is not None:
        cat.is_accessory = bool(payload["is_accessory"])
    if "spec_fields" in payload and payload["spec_fields"] is not None:
        cat.spec_fields = _clean_spec_fields(payload["spec_fields"])
    if "sort_order" in payload and payload["sort_order"] is not None:
        cat.sort_order = int(payload["sort_order"])
    if "is_active" in payload and payload["is_active"] is not None:
        cat.is_active = bool(payload["is_active"])
    await db.commit()
    await db.refresh(cat)
    return cat


async def _require_category(db: AsyncSession, code: str) -> AssetCategory:
    await ensure_default_categories(db)
    cat = (
        await db.execute(select(AssetCategory).where(AssetCategory.code == code))
    ).scalar_one_or_none()
    if not cat:
        raise ValidationError(f"Unknown asset category '{code}'")
    return cat


def _check_condition(value: Optional[str]) -> None:
    if value is not None and value not in ASSET_CONDITIONS:
        raise ValidationError(
            "Condition must be one of: " + ", ".join(ASSET_CONDITIONS)
        )


async def _check_parent(
    db: AsyncSession, parent_id: Optional[int], asset_id: Optional[int] = None
) -> None:
    if parent_id is None:
        return
    if asset_id is not None and parent_id == asset_id:
        raise ValidationError("An asset can't be an accessory of itself")
    parent = await get_asset(db, parent_id)
    if parent.parent_asset_id is not None:
        raise ValidationError(
            f"{parent.asset_tag} is itself an accessory — link to its main asset"
        )


async def create_asset(db: AsyncSession, *, payload: dict) -> Asset:
    payload = {k: v for k, v in payload.items() if v is not None or k == "parent_asset_id"}
    payload["asset_tag"] = payload["asset_tag"].strip()
    if (
        await db.execute(
            select(Asset).where(Asset.asset_tag == payload["asset_tag"])
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Asset tag '{payload['asset_tag']}' exists")
    await _require_category(db, payload.get("category", "other"))
    _check_condition(payload.get("condition"))
    await _check_parent(db, payload.get("parent_asset_id"))
    asset = Asset(**payload, status="in_stock")
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def list_assets(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    category: Optional[str] = None,
    condition: Optional[str] = None,
    usable: Optional[bool] = None,
    search: Optional[str] = None,
) -> Sequence[Asset]:
    stmt = select(Asset)
    if status:
        stmt = stmt.where(Asset.status == status)
    if assigned_to is not None:
        stmt = stmt.where(Asset.assigned_to == assigned_to)
    if category:
        stmt = stmt.where(Asset.category == category)
    if condition:
        stmt = stmt.where(Asset.condition == condition)
    if usable is True:
        stmt = stmt.where(Asset.condition == "working")
    elif usable is False:
        stmt = stmt.where(Asset.condition != "working")
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Asset.asset_tag.ilike(like),
                Asset.name.ilike(like),
                Asset.brand.ilike(like),
                Asset.model.ilike(like),
                Asset.serial_number.ilike(like),
                Asset.notes.ilike(like),
            )
        )
    stmt = stmt.order_by(Asset.created_at.desc(), Asset.id.desc())
    return (await db.execute(stmt)).scalars().all()


async def asset_summary(db: AsyncSession) -> dict:
    """Counts for the register header."""
    rows = (await db.execute(select(Asset.status, Asset.condition))).all()
    out = {
        "total": len(rows),
        "in_stock_usable": 0,
        "assigned": 0,
        "not_usable": 0,
        "in_repair": 0,
        "lost": 0,
        "retired": 0,
    }
    for status, condition in rows:
        if status == "assigned":
            out["assigned"] += 1
        elif status in ("in_repair", "lost", "retired"):
            out[status] += 1
        elif status == "in_stock" and condition == "working":
            out["in_stock_usable"] += 1
        if condition != "working":
            out["not_usable"] += 1
    return out


async def get_asset(db: AsyncSession, asset_id: int) -> Asset:
    a = (
        await db.execute(select(Asset).where(Asset.id == asset_id))
    ).scalar_one_or_none()
    if not a:
        raise NotFoundError("Asset not found")
    return a


async def _accessories(db: AsyncSession, asset_id: int) -> Sequence[Asset]:
    return (
        await db.execute(select(Asset).where(Asset.parent_asset_id == asset_id))
    ).scalars().all()


_STATUS_EDITS = {"in_stock", "in_repair", "retired", "lost"}


async def update_asset(
    db: AsyncSession, asset_id: int, *, payload: dict
) -> Asset:
    asset = await get_asset(db, asset_id)
    allowed = {
        "name", "category", "brand", "model", "specs", "parent_asset_id",
        "serial_number", "purchase_date", "purchase_cost", "warranty_until",
        "condition", "status", "notes",
    }
    # Explicit nulls clear these; elsewhere null means "unchanged".
    clearable = {
        "brand", "model", "specs", "parent_asset_id", "serial_number",
        "purchase_date", "purchase_cost", "warranty_until", "notes",
    }
    if payload.get("category"):
        await _require_category(db, payload["category"])
    _check_condition(payload.get("condition"))
    if "parent_asset_id" in payload:
        await _check_parent(db, payload["parent_asset_id"], asset.id)
    if payload.get("status") is not None:
        new_status = payload["status"]
        if new_status not in _STATUS_EDITS:
            raise ValidationError("Use Assign / Return to change assignment")
        if asset.status == "assigned":
            raise ValidationError("Return the asset before changing its status")
    for k, v in payload.items():
        if k not in allowed:
            continue
        if v is None and k not in clearable:
            continue
        setattr(asset, k, v)
    await db.commit()
    await db.refresh(asset)
    return asset


async def assign_asset(
    db: AsyncSession,
    asset_id: int,
    *,
    employee_id: int,
    notes: Optional[str],
    assigned_by_user_id: Optional[int],
    include_accessories: bool = True,
) -> Asset:
    asset = await get_asset(db, asset_id)
    if asset.status != "in_stock":
        raise ValidationError(
            f"Cannot assign an asset with status '{asset.status}'"
        )
    if not asset.is_usable:
        raise ValidationError(
            f"{asset.asset_tag} is marked '{asset.condition.replace('_', ' ')}' "
            "and can't be handed out"
        )
    employee = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee not found")
    if employee.exit_date and employee.exit_date < _now().date():
        raise ValidationError("This employee has already left")

    targets = [asset]
    if include_accessories:
        targets += [
            a for a in await _accessories(db, asset.id)
            if a.status == "in_stock" and a.is_usable
        ]
    now = _now()
    for a in targets:
        a.status = "assigned"
        a.assigned_to = employee_id
        a.assigned_at = now
        db.add(
            AssetAssignment(
                asset_id=a.id,
                employee_id=employee_id,
                assigned_at=now,
                notes=notes if a is asset else f"With {asset.asset_tag}",
                assigned_by=assigned_by_user_id,
            )
        )
    await db.commit()
    await db.refresh(asset)
    return asset


async def _return_one(
    db: AsyncSession,
    asset: Asset,
    *,
    return_condition: str,
    notes: Optional[str],
    received_by: Optional[int],
) -> None:
    open_assignment = (
        await db.execute(
            select(AssetAssignment)
            .where(AssetAssignment.asset_id == asset.id)
            .where(AssetAssignment.returned_at.is_(None))
            .order_by(AssetAssignment.assigned_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if open_assignment:
        open_assignment.returned_at = _now()
        open_assignment.return_condition = return_condition
        open_assignment.received_by = received_by
        if notes:
            open_assignment.notes = (
                (open_assignment.notes + "\n") if open_assignment.notes else ""
            ) + f"Return: {notes}"
    asset.assigned_to = None
    asset.assigned_at = None
    if return_condition == "lost":
        asset.status = "lost"
    else:
        asset.condition = return_condition
        # Damaged / not-working items go for repair; expired ones are
        # kept on the shelf but can't be handed out again.
        asset.status = (
            "in_repair" if return_condition in ("damaged", "not_working") else "in_stock"
        )


async def return_asset(
    db: AsyncSession,
    asset_id: int,
    *,
    return_condition: str,
    notes: Optional[str],
    received_by: Optional[int] = None,
    include_accessories: bool = True,
) -> Asset:
    if return_condition not in RETURN_CONDITIONS:
        raise ValidationError(
            "Return condition must be one of: " + ", ".join(RETURN_CONDITIONS)
        )
    asset = await get_asset(db, asset_id)
    if asset.status != "assigned":
        raise ValidationError("Asset is not currently assigned")
    employee_id = asset.assigned_to
    await _return_one(
        db, asset, return_condition=return_condition, notes=notes,
        received_by=received_by,
    )
    if include_accessories:
        for acc in await _accessories(db, asset.id):
            if acc.status == "assigned" and acc.assigned_to == employee_id:
                # Accessories come back in working order unless the main
                # item was lost with them.
                await _return_one(
                    db, acc,
                    return_condition="lost" if return_condition == "lost" else "working",
                    notes=f"With {asset.asset_tag}",
                    received_by=received_by,
                )
    await db.commit()
    await db.refresh(asset)
    if employee_id is not None:
        from app.services import asset_clearance

        await asset_clearance.on_assets_changed(db, employee_id, returned=[asset])
    return asset


RETIRE_REASONS = {
    "expired": "End of life",
    "damaged": "Damaged beyond repair",
    "sold": "Sold",
    "disposed": "Disposed / scrapped",
    "donated": "Donated",
    "other": "Other",
}


def _append_note(asset: Asset, line: str) -> None:
    asset.notes = f"{asset.notes}\n{line}" if asset.notes else line


async def retire_asset(
    db: AsyncSession, asset_id: int, *, reason: str, notes: Optional[str] = None
) -> Asset:
    """Mark an asset as no longer available. It stays on the register
    (with its history) but can't be assigned until restored."""
    if reason not in RETIRE_REASONS:
        raise ValidationError("Unknown reason")
    asset = await get_asset(db, asset_id)
    if asset.status == "assigned":
        raise ValidationError("Take the asset back before retiring it")
    if asset.status == "retired":
        return asset
    asset.status = "retired"
    if reason in ("expired", "damaged"):
        asset.condition = reason
    stamp = _now().strftime("%d %b %Y")
    _append_note(
        asset,
        f"Retired {stamp}: {RETIRE_REASONS[reason]}" + (f" — {notes.strip()}" if notes and notes.strip() else ""),
    )
    await db.commit()
    await db.refresh(asset)
    return asset


async def restore_asset(db: AsyncSession, asset_id: int) -> Asset:
    """Bring a retired / lost asset back into stock."""
    asset = await get_asset(db, asset_id)
    if asset.status not in ("retired", "lost"):
        raise ValidationError("Only retired or lost assets can be restored")
    asset.status = "in_stock"
    _append_note(asset, f"Restored to stock {_now().strftime('%d %b %Y')}")
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete_asset(db: AsyncSession, asset_id: int) -> None:
    """Remove an asset entered by mistake. Anything that was ever handed
    to someone keeps its record (exit clearance, audits) — retire it."""
    asset = await get_asset(db, asset_id)
    if asset.status == "assigned":
        raise ValidationError("Take the asset back first — then retire it")
    used = (
        await db.execute(
            select(AssetAssignment.id).where(AssetAssignment.asset_id == asset_id).limit(1)
        )
    ).first()
    if used:
        raise ConflictError(
            "This asset has assignment history, so it can't be deleted. "
            "Retire it instead to mark it as no longer available."
        )
    for acc in await _accessories(db, asset_id):
        acc.parent_asset_id = None
    await db.delete(asset)
    await db.commit()


async def list_assignment_history(
    db: AsyncSession, asset_id: int
) -> Sequence[AssetAssignment]:
    return (
        await db.execute(
            select(AssetAssignment)
            .where(AssetAssignment.asset_id == asset_id)
            .order_by(AssetAssignment.assigned_at.desc())
        )
    ).scalars().all()


async def employee_asset_history(
    db: AsyncSession, employee_id: int
) -> Sequence[tuple[AssetAssignment, Asset]]:
    """Every assignment an employee has had, newest first."""
    return (
        await db.execute(
            select(AssetAssignment, Asset)
            .join(Asset, Asset.id == AssetAssignment.asset_id)
            .where(AssetAssignment.employee_id == employee_id)
            .order_by(AssetAssignment.assigned_at.desc())
        )
    ).all()


# ─── Visitors ────────────────────────────────────────────────────────
async def pre_register_visitor(
    db: AsyncSession,
    *,
    host_employee: Employee,
    payload: dict,
) -> Visitor:
    visitor = Visitor(
        host_employee_id=host_employee.id,
        qr_token=secrets.token_urlsafe(16),
        status="scheduled",
        **payload,
    )
    db.add(visitor)
    await db.commit()
    await db.refresh(visitor)
    return visitor


async def my_visitors(
    db: AsyncSession,
    *,
    host_employee_id: int,
    status: Optional[str] = None,
) -> Sequence[Visitor]:
    stmt = select(Visitor).where(Visitor.host_employee_id == host_employee_id)
    if status:
        stmt = stmt.where(Visitor.status == status)
    stmt = stmt.order_by(Visitor.expected_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def list_today_visitors(
    db: AsyncSession,
) -> Sequence[Visitor]:
    today = _now().date()
    return (
        await db.execute(
            select(Visitor)
            .where(Visitor.expected_at >= datetime.combine(today, datetime.min.time()))
            .where(Visitor.expected_at <= datetime.combine(today, datetime.max.time()))
            .order_by(Visitor.expected_at.asc())
        )
    ).scalars().all()


async def list_visitors(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    host_employee_id: Optional[int] = None,
    search: Optional[str] = None,
    from_date=None,
    to_date=None,
) -> Sequence[Visitor]:
    from sqlalchemy import or_

    stmt = select(Visitor)
    if status:
        stmt = stmt.where(Visitor.status == status)
    if host_employee_id is not None:
        stmt = stmt.where(Visitor.host_employee_id == host_employee_id)
    if from_date is not None:
        stmt = stmt.where(
            Visitor.expected_at >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date is not None:
        stmt = stmt.where(
            Visitor.expected_at <= datetime.combine(to_date, datetime.max.time())
        )
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Visitor.full_name.ilike(like),
                Visitor.contact_phone.ilike(like),
                Visitor.contact_email.ilike(like),
                Visitor.company.ilike(like),
                Visitor.purpose.ilike(like),
            )
        )
    stmt = stmt.order_by(Visitor.expected_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_visitor_by_token(
    db: AsyncSession, qr_token: str
) -> Visitor:
    visitor = (
        await db.execute(select(Visitor).where(Visitor.qr_token == qr_token))
    ).scalar_one_or_none()
    if not visitor:
        raise NotFoundError("Invalid QR code")
    return visitor


async def visitor_check_in(
    db: AsyncSession,
    *,
    qr_token: str,
    badge_number: Optional[str] = None,
) -> Visitor:
    visitor = (
        await db.execute(select(Visitor).where(Visitor.qr_token == qr_token))
    ).scalar_one_or_none()
    if not visitor:
        raise NotFoundError("Invalid QR code")
    if visitor.status not in ("scheduled", "checked_in"):
        raise ValidationError(
            f"Cannot check in a visitor with status '{visitor.status}'"
        )
    if visitor.checked_in_at is None:
        visitor.checked_in_at = _now()
    visitor.status = "checked_in"
    if badge_number:
        visitor.badge_number = badge_number
    await db.commit()
    await db.refresh(visitor)
    return visitor


async def visitor_check_out(
    db: AsyncSession, visitor_id: int
) -> Visitor:
    visitor = (
        await db.execute(select(Visitor).where(Visitor.id == visitor_id))
    ).scalar_one_or_none()
    if not visitor:
        raise NotFoundError("Visitor not found")
    if visitor.status != "checked_in":
        raise ValidationError("Visitor must be checked in first")
    visitor.checked_out_at = _now()
    visitor.status = "checked_out"
    await db.commit()
    await db.refresh(visitor)
    return visitor


# ─── Meeting rooms ───────────────────────────────────────────────────
async def create_room(db: AsyncSession, *, payload: dict) -> MeetingRoom:
    if (
        await db.execute(
            select(MeetingRoom).where(MeetingRoom.code == payload["code"])
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Room code '{payload['code']}' exists")
    room = MeetingRoom(**payload, is_active=True)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def list_rooms(db: AsyncSession) -> Sequence[MeetingRoom]:
    return (
        await db.execute(
            select(MeetingRoom)
            .where(MeetingRoom.is_active.is_(True))
            .order_by(MeetingRoom.name.asc())
        )
    ).scalars().all()


async def book_room(
    db: AsyncSession,
    *,
    booker: Employee,
    payload: dict,
) -> RoomBooking:
    if payload["end_time"] <= payload["start_time"]:
        raise ValidationError("end_time must be after start_time")
    room = (
        await db.execute(
            select(MeetingRoom).where(MeetingRoom.id == payload["room_id"])
        )
    ).scalar_one_or_none()
    if not room or not room.is_active:
        raise NotFoundError("Room not found or inactive")

    overlap = (
        await db.execute(
            select(RoomBooking)
            .where(RoomBooking.room_id == room.id)
            .where(RoomBooking.status != "cancelled")
            .where(RoomBooking.start_time < payload["end_time"])
            .where(RoomBooking.end_time > payload["start_time"])
        )
    ).scalars().all()
    if overlap:
        raise ConflictError(
            f"Room is already booked in this slot ({len(overlap)} clash)"
        )

    booking = RoomBooking(
        booked_by_employee_id=booker.id,
        status="booked",
        **payload,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def list_bookings(
    db: AsyncSession,
    *,
    room_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    upcoming_only: bool = False,
) -> Sequence[RoomBooking]:
    stmt = select(RoomBooking)
    if room_id is not None:
        stmt = stmt.where(RoomBooking.room_id == room_id)
    if employee_id is not None:
        stmt = stmt.where(RoomBooking.booked_by_employee_id == employee_id)
    if upcoming_only:
        stmt = stmt.where(RoomBooking.end_time >= _now())
    stmt = stmt.order_by(RoomBooking.start_time.asc())
    return (await db.execute(stmt)).scalars().all()


async def cancel_booking(
    db: AsyncSession, booking_id: int, *, employee: Employee
) -> RoomBooking:
    booking = (
        await db.execute(
            select(RoomBooking).where(RoomBooking.id == booking_id)
        )
    ).scalar_one_or_none()
    if not booking:
        raise NotFoundError("Booking not found")
    if booking.booked_by_employee_id != employee.id:
        raise ForbiddenError("Only the booker can cancel this booking")
    if booking.status == "cancelled":
        return booking
    booking.status = "cancelled"
    await db.commit()
    await db.refresh(booking)
    return booking


# ─── Job postings + applications ─────────────────────────────────────
async def create_posting(
    db: AsyncSession,
    *,
    payload: dict,
    posted_by_user_id: Optional[int],
) -> JobPosting:
    if (
        await db.execute(
            select(JobPosting).where(JobPosting.code == payload["code"])
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Posting '{payload['code']}' exists")
    posting = JobPosting(
        **payload,
        status="draft",
        posted_at=_now(),
        posted_by=posted_by_user_id,
    )
    db.add(posting)
    await db.commit()
    await db.refresh(posting)
    return posting


async def list_postings(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    search: Optional[str] = None,
    published_to_app: Optional[bool] = None,
) -> Sequence[JobPosting]:
    from sqlalchemy import or_

    stmt = select(JobPosting)
    if status:
        stmt = stmt.where(JobPosting.status == status)
    if published_to_app is not None:
        stmt = stmt.where(JobPosting.published_to_app == published_to_app)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                JobPosting.code.ilike(like),
                JobPosting.title.ilike(like),
                JobPosting.location.ilike(like),
                JobPosting.description.ilike(like),
            )
        )
    stmt = stmt.order_by(JobPosting.posted_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def update_posting(
    db: AsyncSession, posting_id: int, *, payload: dict
) -> JobPosting:
    p = await get_posting(db, posting_id)
    allowed = {
        "title", "department_id", "location", "employment_type",
        "description", "requirements", "referral_bonus", "is_internal_only",
        "published_to_app", "closes_on",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return p


async def get_posting(db: AsyncSession, posting_id: int) -> JobPosting:
    p = (
        await db.execute(select(JobPosting).where(JobPosting.id == posting_id))
    ).scalar_one_or_none()
    if not p:
        raise NotFoundError("Posting not found")
    return p


async def update_posting_status(
    db: AsyncSession, posting_id: int, *, status: str
) -> JobPosting:
    p = await get_posting(db, posting_id)
    p.status = status
    await db.commit()
    await db.refresh(p)
    return p


async def apply_to_posting(
    db: AsyncSession,
    *,
    posting: JobPosting,
    applicant: Employee,
    payload: dict,
) -> JobApplication:
    if posting.status != "published":
        raise ValidationError("Posting is not open for applications")
    referrer_id = payload.get("referrer_employee_id")
    if referrer_id == applicant.id:
        raise ValidationError("You cannot refer yourself")
    if referrer_id is not None:
        referrer = (
            await db.execute(select(Employee).where(Employee.id == referrer_id))
        ).scalar_one_or_none()
        if not referrer:
            raise NotFoundError("Referrer employee not found")
    existing = (
        await db.execute(
            select(JobApplication)
            .where(JobApplication.posting_id == posting.id)
            .where(JobApplication.applicant_employee_id == applicant.id)
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("You have already applied to this posting")
    app = JobApplication(
        posting_id=posting.id,
        applicant_employee_id=applicant.id,
        referrer_employee_id=referrer_id,
        cover_note=payload.get("cover_note"),
        resume_url=payload.get("resume_url"),
        status="submitted",
        submitted_at=_now(),
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def update_application_status(
    db: AsyncSession,
    application_id: int,
    *,
    status: str,
) -> JobApplication:
    app = (
        await db.execute(
            select(JobApplication).where(JobApplication.id == application_id)
        )
    ).scalar_one_or_none()
    if not app:
        raise NotFoundError("Application not found")
    app.status = status
    if status == "hired" and app.referrer_employee_id and not app.referral_bonus_paid:
        # Mark eligible — actual payroll posting is left to a downstream job.
        app.referral_bonus_paid = False
    await db.commit()
    await db.refresh(app)
    return app


async def list_applications_for_posting(
    db: AsyncSession, posting_id: int
) -> Sequence[JobApplication]:
    return (
        await db.execute(
            select(JobApplication)
            .where(JobApplication.posting_id == posting_id)
            .order_by(JobApplication.submitted_at.desc())
        )
    ).scalars().all()


async def my_applications(
    db: AsyncSession, applicant_employee_id: int
) -> Sequence[JobApplication]:
    return (
        await db.execute(
            select(JobApplication)
            .where(
                JobApplication.applicant_employee_id == applicant_employee_id
            )
            .order_by(JobApplication.submitted_at.desc())
        )
    ).scalars().all()


async def my_referrals(
    db: AsyncSession, referrer_employee_id: int
) -> Sequence[JobApplication]:
    return (
        await db.execute(
            select(JobApplication)
            .where(
                JobApplication.referrer_employee_id == referrer_employee_id
            )
            .order_by(JobApplication.submitted_at.desc())
        )
    ).scalars().all()

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
async def create_asset(db: AsyncSession, *, payload: dict) -> Asset:
    if (
        await db.execute(
            select(Asset).where(Asset.asset_tag == payload["asset_tag"])
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Asset tag '{payload['asset_tag']}' exists")
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
) -> Sequence[Asset]:
    stmt = select(Asset)
    if status:
        stmt = stmt.where(Asset.status == status)
    if assigned_to is not None:
        stmt = stmt.where(Asset.assigned_to == assigned_to)
    if category:
        stmt = stmt.where(Asset.category == category)
    stmt = stmt.order_by(Asset.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_asset(db: AsyncSession, asset_id: int) -> Asset:
    a = (
        await db.execute(select(Asset).where(Asset.id == asset_id))
    ).scalar_one_or_none()
    if not a:
        raise NotFoundError("Asset not found")
    return a


async def assign_asset(
    db: AsyncSession,
    asset_id: int,
    *,
    employee_id: int,
    notes: Optional[str],
    assigned_by_user_id: Optional[int],
) -> Asset:
    asset = await get_asset(db, asset_id)
    if asset.status != "in_stock":
        raise ValidationError(
            f"Cannot assign an asset with status '{asset.status}'"
        )
    employee = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee not found")
    asset.status = "assigned"
    asset.assigned_to = employee_id
    asset.assigned_at = _now()
    db.add(
        AssetAssignment(
            asset_id=asset.id,
            employee_id=employee_id,
            assigned_at=_now(),
            notes=notes,
            assigned_by=assigned_by_user_id,
        )
    )
    await db.commit()
    await db.refresh(asset)
    return asset


async def return_asset(
    db: AsyncSession,
    asset_id: int,
    *,
    return_condition: str,
    notes: Optional[str],
) -> Asset:
    asset = await get_asset(db, asset_id)
    if asset.status != "assigned":
        raise ValidationError("Asset is not currently assigned")
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
        if notes:
            open_assignment.notes = (open_assignment.notes or "") + f"\nReturn: {notes}"
    asset.assigned_to = None
    asset.assigned_at = None
    if return_condition == "lost":
        asset.status = "lost"
    elif return_condition == "damaged":
        asset.status = "in_repair"
        asset.condition = "damaged"
    else:
        asset.status = "in_stock"
        asset.condition = return_condition
    await db.commit()
    await db.refresh(asset)
    return asset


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
) -> Sequence[JobPosting]:
    stmt = select(JobPosting)
    if status:
        stmt = stmt.where(JobPosting.status == status)
    stmt = stmt.order_by(JobPosting.posted_at.desc())
    return (await db.execute(stmt)).scalars().all()


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

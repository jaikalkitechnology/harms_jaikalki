from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.polish import (
    AssetAssignRequest,
    AssetAssignmentOut,
    AssetCreate,
    AssetOut,
    AssetReturnRequest,
    JobApplicationCreate,
    JobApplicationOut,
    JobApplicationStatusUpdate,
    JobPostingCreate,
    JobPostingOut,
    JobPostingStatusUpdate,
    MeetingRoomCreate,
    MeetingRoomOut,
    RoomBookingCreate,
    RoomBookingOut,
    VisitorCheckIn,
    VisitorCreate,
    VisitorOut,
)
from app.services import employee_service as emp_svc
from app.services import polish_service as polish

router = APIRouter(prefix="/polish", tags=["polish"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ─── Assets ──────────────────────────────────────────────────────────
@router.get("/assets", response_model=list[AssetOut])
async def list_assets(
    asset_status: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.view")),
):
    return await polish.list_assets(
        db, status=asset_status, category=category
    )


@router.post(
    "/assets",
    response_model=AssetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.create_asset(db, payload=payload.model_dump())


@router.get("/assets/me", response_model=list[AssetOut])
async def my_assets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.list_assets(db, assigned_to=emp.id)


@router.post(
    "/assets/{asset_id}/assign",
    response_model=AssetOut,
)
async def assign_asset(
    asset_id: int,
    payload: AssetAssignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.assign_asset(
        db,
        asset_id,
        employee_id=payload.employee_id,
        notes=payload.notes,
        assigned_by_user_id=user.id,
    )


@router.post("/assets/{asset_id}/return", response_model=AssetOut)
async def return_asset(
    asset_id: int,
    payload: AssetReturnRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.return_asset(
        db,
        asset_id,
        return_condition=payload.return_condition,
        notes=payload.notes,
    )


@router.get(
    "/assets/{asset_id}/history",
    response_model=list[AssetAssignmentOut],
)
async def asset_history(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.view")),
):
    return await polish.list_assignment_history(db, asset_id)


# ─── Visitors ────────────────────────────────────────────────────────
@router.post(
    "/visitors",
    response_model=VisitorOut,
    status_code=status.HTTP_201_CREATED,
)
async def pre_register_visitor(
    payload: VisitorCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.pre_register_visitor(
        db, host_employee=emp, payload=payload.model_dump()
    )


@router.get("/visitors/me", response_model=list[VisitorOut])
async def my_visitors(
    visitor_status: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.my_visitors(
        db, host_employee_id=emp.id, status=visitor_status
    )


@router.get("/visitors/today", response_model=list[VisitorOut])
async def today_visitors(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.view")),
):
    return await polish.list_today_visitors(db)


@router.post("/visitors/check-in", response_model=VisitorOut)
async def visitor_check_in(
    payload: VisitorCheckIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.view")),
):
    return await polish.visitor_check_in(
        db, qr_token=payload.qr_token, badge_number=payload.badge_number
    )


@router.post("/visitors/{visitor_id}/check-out", response_model=VisitorOut)
async def visitor_check_out(
    visitor_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.view")),
):
    return await polish.visitor_check_out(db, visitor_id)


# ─── Meeting rooms ───────────────────────────────────────────────────
@router.get("/rooms", response_model=list[MeetingRoomOut])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await polish.list_rooms(db)


@router.post(
    "/rooms",
    response_model=MeetingRoomOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    payload: MeetingRoomCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.create_room(db, payload=payload.model_dump())


@router.post(
    "/rooms/bookings",
    response_model=RoomBookingOut,
    status_code=status.HTTP_201_CREATED,
)
async def book_room(
    payload: RoomBookingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.book_room(
        db, booker=emp, payload=payload.model_dump()
    )


@router.get("/rooms/bookings", response_model=list[RoomBookingOut])
async def list_bookings(
    room_id: Optional[int] = None,
    upcoming_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await polish.list_bookings(
        db, room_id=room_id, upcoming_only=upcoming_only
    )


@router.get(
    "/rooms/bookings/me", response_model=list[RoomBookingOut]
)
async def my_bookings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.list_bookings(db, employee_id=emp.id)


@router.post(
    "/rooms/bookings/{booking_id}/cancel", response_model=RoomBookingOut
)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.cancel_booking(db, booking_id, employee=emp)


# ─── Job postings + applications ─────────────────────────────────────
@router.get("/jobs", response_model=list[JobPostingOut])
async def list_postings(
    posting_status: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await polish.list_postings(db, status=posting_status)


@router.post(
    "/jobs",
    response_model=JobPostingOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_posting(
    payload: JobPostingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.create_posting(
        db, payload=payload.model_dump(), posted_by_user_id=user.id
    )


@router.patch(
    "/jobs/{posting_id}/status", response_model=JobPostingOut
)
async def update_posting_status(
    posting_id: int,
    payload: JobPostingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.update_posting_status(
        db, posting_id, status=payload.status
    )


@router.post(
    "/jobs/{posting_id}/apply",
    response_model=JobApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_posting(
    posting_id: int,
    payload: JobApplicationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    posting = await polish.get_posting(db, posting_id)
    emp = await _self_employee(db, user)
    return await polish.apply_to_posting(
        db, posting=posting, applicant=emp, payload=payload.model_dump()
    )


@router.get(
    "/jobs/{posting_id}/applications",
    response_model=list[JobApplicationOut],
)
async def list_applications(
    posting_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.list_applications_for_posting(db, posting_id)


@router.patch(
    "/jobs/applications/{application_id}/status",
    response_model=JobApplicationOut,
)
async def update_application_status(
    application_id: int,
    payload: JobApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await polish.update_application_status(
        db, application_id, status=payload.status
    )


@router.get("/jobs/me/applications", response_model=list[JobApplicationOut])
async def my_applications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.my_applications(db, emp.id)


@router.get("/jobs/me/referrals", response_model=list[JobApplicationOut])
async def my_referrals(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await polish.my_referrals(db, emp.id)

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission, require_role, Role as RoleEnum
from app.dependencies import get_current_user, get_db
from app.models import Customer, FieldJob, User, Visit
from app.schemas.field_force import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    FieldExpenseCreate,
    FieldExpenseOut,
    FieldJobCreate,
    FieldJobOut,
    LiveMapEntry,
    LocationTrackIn,
    LocationTrackOut,
    TeamPerformanceEntry,
    VisitCheckIn,
    VisitCheckOut,
    VisitFormSubmit,
    VisitOut,
    VisitPhotoCreate,
    VisitPhotoOut,
)
from app.services import employee_service as emp_svc
from app.services import field_force_service as ff_svc

router = APIRouter(prefix="/field", tags=["field"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ─── Customers ────────────────────────────────────────────────────────
@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(
    territory: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await ff_svc.list_customers(
        db, territory=territory, search=search
    )


@router.post(
    "/customers",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ff_svc.create_customer(
        db, payload=payload.model_dump(), created_by=user.id
    )


@router.get("/customers/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await ff_svc.get_customer(db, customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await ff_svc.update_customer(
        db, customer_id, payload.model_dump(exclude_unset=True)
    )


# ─── Field jobs ───────────────────────────────────────────────────────
@router.post(
    "/jobs",
    response_model=FieldJobOut,
    status_code=status.HTTP_201_CREATED,
)
async def assign_job(
    payload: FieldJobCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ff_svc.assign_job(
        db,
        employee_id=payload.employee_id,
        customer_id=payload.customer_id,
        job_type=payload.job_type,
        scheduled_date=payload.scheduled_date,
        scheduled_time=payload.scheduled_time,
        priority=payload.priority,
        notes=payload.notes,
        assigned_by=user.id,
    )


@router.get("/jobs/today", response_model=list[FieldJobOut])
async def my_jobs_today(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await ff_svc.list_jobs_for_employee(db, emp.id, on_date=date.today())


@router.get("/jobs/me", response_model=list[FieldJobOut])
async def my_jobs(
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await ff_svc.list_jobs_for_employee(db, emp.id, on_date=on_date)


@router.get("/jobs/{job_id}", response_model=FieldJobOut)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await ff_svc.get_job(db, job_id)


# ─── Visit lifecycle ──────────────────────────────────────────────────
@router.post("/jobs/{job_id}/checkin", response_model=VisitOut)
async def visit_checkin(
    job_id: int,
    payload: VisitCheckIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    job = await ff_svc.get_job(db, job_id)
    return await ff_svc.visit_check_in(
        db,
        job=job,
        employee=emp,
        lat=payload.lat,
        lng=payload.lng,
        is_mock=payload.is_mock,
        selfie_url=payload.selfie_url,
    )


@router.post("/visits/{visit_id}/visit-form", response_model=VisitOut)
async def submit_visit_form(
    visit_id: int,
    payload: VisitFormSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    visit = await ff_svc.get_visit(db, visit_id)
    return await ff_svc.submit_visit_form(
        db, visit=visit, employee=emp, visit_form=payload.visit_form
    )


@router.post(
    "/visits/{visit_id}/photos",
    response_model=VisitPhotoOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_photo(
    visit_id: int,
    payload: VisitPhotoCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    visit = await ff_svc.get_visit(db, visit_id)
    return await ff_svc.add_visit_photo(
        db,
        visit=visit,
        employee=emp,
        photo_url=payload.photo_url,
        photo_type=payload.photo_type,
        geo_lat=payload.geo_lat,
        geo_lng=payload.geo_lng,
        watermarked=payload.watermarked,
    )


@router.post("/visits/{visit_id}/checkout", response_model=VisitOut)
async def visit_checkout(
    visit_id: int,
    payload: VisitCheckOut,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    visit = await ff_svc.get_visit(db, visit_id)
    return await ff_svc.visit_check_out(
        db,
        visit=visit,
        employee=emp,
        lat=payload.lat,
        lng=payload.lng,
        outcome=payload.outcome,
        notes=payload.notes,
        signature_url=payload.signature_url,
    )


@router.get("/visits/{visit_id}", response_model=VisitOut)
async def get_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await ff_svc.get_visit(db, visit_id)


# ─── Location tracking ────────────────────────────────────────────────
@router.post(
    "/location/track",
    response_model=LocationTrackOut,
    status_code=status.HTTP_201_CREATED,
)
async def track_location(
    payload: LocationTrackIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await ff_svc.ingest_location(
        db,
        employee=emp,
        lat=payload.lat,
        lng=payload.lng,
        accuracy_m=payload.accuracy_m,
        speed_mps=payload.speed_mps,
        heading=payload.heading,
        battery_pct=payload.battery_pct,
        is_mock=payload.is_mock,
        timestamp=payload.timestamp,
    )


@router.get("/team/live-map", response_model=list[LiveMapEntry])
async def team_live_map(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    allowed = await emp_svc.visible_employee_ids(db, user)
    return await ff_svc.live_map(db, employee_ids=allowed)


@router.get("/team/performance", response_model=list[TeamPerformanceEntry])
async def team_performance(
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    allowed = await emp_svc.visible_employee_ids(db, user)
    return await ff_svc.team_performance(
        db, employee_ids=allowed, on_date=on_date
    )


# ─── Field expenses ───────────────────────────────────────────────────
@router.post(
    "/expenses",
    response_model=FieldExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_expense(
    payload: FieldExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await ff_svc.create_expense(
        db,
        employee=emp,
        category=payload.category,
        amount=payload.amount,
        expense_date=payload.expense_date,
        visit_id=payload.visit_id,
        receipt_url=payload.receipt_url,
        description=payload.description,
    )


@router.get("/expenses/me", response_model=list[FieldExpenseOut])
async def my_expenses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await ff_svc.list_expenses_for_employee(db, emp.id)

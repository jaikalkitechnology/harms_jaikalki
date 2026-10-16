"""Field force service: customers, jobs, visit lifecycle, GPS tracking."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Customer,
    Employee,
    FieldEmployee,
    FieldExpense,
    FieldJob,
    LocationTrack,
    User,
    Visit,
    VisitPhoto,
)
from app.utils.geo import haversine_distance_m

# Customer geo-fence radius (meters). Field visits must check in within this
# distance of the customer's saved location. Set generous to allow building
# entrance variance.
CUSTOMER_GEO_RADIUS_M = 200


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    return datetime.now(timezone.utc).date()


# ── Customer CRUD ─────────────────────────────────────────────────────
async def create_customer(
    db: AsyncSession, *, payload: dict, created_by: Optional[int] = None
) -> Customer:
    cust = Customer(**payload, created_by=created_by)
    db.add(cust)
    await db.commit()
    await db.refresh(cust)
    return cust


async def list_customers(
    db: AsyncSession,
    *,
    territory: Optional[str] = None,
    type_: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    limit: int = 200,
) -> Sequence[Customer]:
    from sqlalchemy import or_

    stmt = select(Customer)
    if territory:
        stmt = stmt.where(Customer.territory == territory)
    if type_:
        stmt = stmt.where(Customer.type == type_)
    if is_active is not None:
        stmt = stmt.where(Customer.is_active == is_active)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Customer.name.ilike(like),
                Customer.city.ilike(like),
                Customer.address.ilike(like),
                Customer.gst.ilike(like),
                Customer.pan.ilike(like),
                Customer.industry.ilike(like),
                Customer.territory.ilike(like),
            )
        )
    stmt = stmt.order_by(Customer.name.asc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


async def get_customer(db: AsyncSession, customer_id: int) -> Customer:
    cust = (
        await db.execute(select(Customer).where(Customer.id == customer_id))
    ).scalar_one_or_none()
    if not cust:
        raise NotFoundError("Customer not found")
    return cust


async def update_customer(
    db: AsyncSession, customer_id: int, payload: dict
) -> Customer:
    cust = await get_customer(db, customer_id)
    for key, value in payload.items():
        if value is not None:
            setattr(cust, key, value)
    await db.commit()
    await db.refresh(cust)
    return cust


# ── Field jobs ────────────────────────────────────────────────────────
async def assign_job(
    db: AsyncSession,
    *,
    employee_id: int,
    customer_id: int,
    job_type: str,
    scheduled_date: date,
    scheduled_time: Optional[str] = None,
    priority: str = "medium",
    notes: Optional[str] = None,
    assigned_by: Optional[int] = None,
) -> FieldJob:
    emp = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")
    cust = await get_customer(db, customer_id)
    job = FieldJob(
        employee_id=employee_id,
        customer_id=cust.id,
        job_type=job_type,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        priority=priority,
        status="scheduled",
        notes=notes,
        assigned_by=assigned_by,
        assigned_at=_now(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def list_jobs_for_employee(
    db: AsyncSession,
    employee_id: int,
    *,
    on_date: Optional[date] = None,
) -> Sequence[FieldJob]:
    stmt = select(FieldJob).where(FieldJob.employee_id == employee_id)
    if on_date:
        stmt = stmt.where(FieldJob.scheduled_date == on_date)
    stmt = stmt.order_by(FieldJob.scheduled_date.desc(), FieldJob.id.asc())
    return (await db.execute(stmt)).scalars().all()


async def get_job(db: AsyncSession, job_id: int) -> FieldJob:
    job = (
        await db.execute(select(FieldJob).where(FieldJob.id == job_id))
    ).scalar_one_or_none()
    if not job:
        raise NotFoundError("Job not found")
    return job


async def _ensure_field_employee(
    db: AsyncSession, employee_id: int
) -> Optional[FieldEmployee]:
    return (
        await db.execute(
            select(FieldEmployee).where(FieldEmployee.employee_id == employee_id)
        )
    ).scalar_one_or_none()


# ── Visit lifecycle ───────────────────────────────────────────────────
async def visit_check_in(
    db: AsyncSession,
    *,
    job: FieldJob,
    employee: Employee,
    lat: float,
    lng: float,
    is_mock: bool = False,
    selfie_url: Optional[str] = None,
) -> Visit:
    if job.employee_id != employee.id:
        raise ForbiddenError("This job belongs to a different employee")
    if job.status not in ("scheduled", "in_progress"):
        raise ValidationError(f"Cannot check in to a {job.status} job")
    if is_mock:
        raise ValidationError(
            "Mock GPS detected. Disable any location-spoofing app and retry."
        )
    if not selfie_url:
        raise ValidationError("Check-in selfie is required")

    cust = await get_customer(db, job.customer_id)
    distance_m: Optional[int] = None
    if cust.geo_lat is not None and cust.geo_lng is not None:
        d = haversine_distance_m(
            lat, lng, float(cust.geo_lat), float(cust.geo_lng)
        )
        distance_m = int(round(d))
        if distance_m > CUSTOMER_GEO_RADIUS_M:
            raise ValidationError(
                f"Outside customer geo-fence ({distance_m}m from "
                f"{cust.name}; limit {CUSTOMER_GEO_RADIUS_M}m)."
            )

    existing = (
        await db.execute(select(Visit).where(Visit.job_id == job.id))
    ).scalar_one_or_none()
    if existing and existing.check_in_time:
        raise ConflictError("Already checked in to this visit")

    visit = existing or Visit(job_id=job.id, employee_id=employee.id)
    visit.check_in_time = _now()
    visit.check_in_lat = Decimal(str(lat))
    visit.check_in_lng = Decimal(str(lng))
    visit.check_in_distance_m = distance_m
    visit.check_in_selfie_url = selfie_url
    visit.check_in_is_mock = is_mock
    if existing is None:
        db.add(visit)

    job.status = "in_progress"

    # Field-employee status flag
    fe = await _ensure_field_employee(db, employee.id)
    if fe:
        fe.current_status = "on_visit"

    await db.commit()
    await db.refresh(visit)
    return visit


async def submit_visit_form(
    db: AsyncSession,
    *,
    visit: Visit,
    employee: Employee,
    visit_form: dict,
) -> Visit:
    if visit.employee_id != employee.id:
        raise ForbiddenError("Not your visit")
    if not visit.check_in_time:
        raise ValidationError("Check in before submitting visit form")
    if visit.check_out_time:
        raise ValidationError("Visit already closed")
    visit.visit_form = visit_form
    await db.commit()
    await db.refresh(visit)
    return visit


async def add_visit_photo(
    db: AsyncSession,
    *,
    visit: Visit,
    employee: Employee,
    photo_url: str,
    photo_type: str = "other",
    geo_lat: Optional[float] = None,
    geo_lng: Optional[float] = None,
    watermarked: bool = False,
) -> VisitPhoto:
    if visit.employee_id != employee.id:
        raise ForbiddenError("Not your visit")
    if not visit.check_in_time:
        raise ValidationError("Check in before uploading photos")
    photo = VisitPhoto(
        visit_id=visit.id,
        photo_url=photo_url,
        photo_type=photo_type,
        geo_lat=Decimal(str(geo_lat)) if geo_lat is not None else None,
        geo_lng=Decimal(str(geo_lng)) if geo_lng is not None else None,
        watermarked=watermarked,
        taken_at=_now(),
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


async def visit_check_out(
    db: AsyncSession,
    *,
    visit: Visit,
    employee: Employee,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    outcome: Optional[str] = None,
    notes: Optional[str] = None,
    signature_url: Optional[str] = None,
) -> Visit:
    if visit.employee_id != employee.id:
        raise ForbiddenError("Not your visit")
    if not visit.check_in_time:
        raise ValidationError("Visit was never checked in")
    if visit.check_out_time:
        raise ConflictError("Visit already closed")

    visit.check_out_time = _now()
    if lat is not None:
        visit.check_out_lat = Decimal(str(lat))
    if lng is not None:
        visit.check_out_lng = Decimal(str(lng))
    if outcome is not None:
        visit.outcome = outcome
    if notes is not None:
        visit.notes = notes
    if signature_url is not None:
        visit.signature_url = signature_url
    visit.duration_minutes = int(
        (visit.check_out_time - visit.check_in_time).total_seconds() // 60
    )

    job = await get_job(db, visit.job_id)
    job.status = "completed"

    fe = await _ensure_field_employee(db, employee.id)
    if fe:
        fe.current_status = "idle"

    await db.commit()
    await db.refresh(visit)
    from app.services.sales_service import refresh_targets_for

    await refresh_targets_for(db, employee.id)
    return visit


async def get_visit(db: AsyncSession, visit_id: int) -> Visit:
    visit = (
        await db.execute(select(Visit).where(Visit.id == visit_id))
    ).scalar_one_or_none()
    if not visit:
        raise NotFoundError("Visit not found")
    return visit


# ── Location tracking ─────────────────────────────────────────────────
async def ingest_location(
    db: AsyncSession,
    *,
    employee: Employee,
    lat: float,
    lng: float,
    accuracy_m: Optional[int] = None,
    speed_mps: Optional[float] = None,
    heading: Optional[float] = None,
    battery_pct: Optional[int] = None,
    is_mock: bool = False,
    timestamp: Optional[datetime] = None,
) -> LocationTrack:
    if is_mock:
        raise ValidationError(
            "Mock GPS detected. Location update rejected."
        )
    track = LocationTrack(
        employee_id=employee.id,
        lat=Decimal(str(lat)),
        lng=Decimal(str(lng)),
        accuracy_m=accuracy_m,
        speed_mps=Decimal(str(speed_mps)) if speed_mps is not None else None,
        heading=Decimal(str(heading)) if heading is not None else None,
        battery_pct=battery_pct,
        is_mock=is_mock,
        timestamp=timestamp or _now(),
    )
    db.add(track)
    await db.commit()
    await db.refresh(track)
    return track


async def live_map(
    db: AsyncSession,
    *,
    employee_ids: Optional[set[int]] = None,
) -> list[dict]:
    """Latest known location per field employee."""
    # Subquery: latest timestamp per employee
    sub = (
        select(
            LocationTrack.employee_id.label("eid"),
            func.max(LocationTrack.timestamp).label("ts"),
        )
        .group_by(LocationTrack.employee_id)
        .subquery()
    )
    stmt = (
        select(LocationTrack, Employee, FieldEmployee)
        .join(
            sub,
            and_(
                LocationTrack.employee_id == sub.c.eid,
                LocationTrack.timestamp == sub.c.ts,
            ),
        )
        .join(Employee, Employee.id == LocationTrack.employee_id)
        .outerjoin(FieldEmployee, FieldEmployee.employee_id == Employee.id)
    )
    if employee_ids is not None:
        if not employee_ids:
            return []
        stmt = stmt.where(LocationTrack.employee_id.in_(employee_ids))
    rows = (await db.execute(stmt)).all()

    now = datetime.utcnow()
    out: list[dict] = []
    for track, emp, fe in rows:
        # Treat the rep as "online" if we received a ping in the last
        # 5 minutes — anything older is considered stale.
        ago_seconds = max(0, int((now - track.timestamp).total_seconds()))
        out.append(
            {
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "lat": float(track.lat),
                "lng": float(track.lng),
                "timestamp": track.timestamp,
                "battery_pct": track.battery_pct,
                "current_status": fe.current_status if fe else "idle",
                "last_visit_customer": None,
                "is_online": ago_seconds <= 5 * 60,
                "last_seen_minutes": ago_seconds // 60,
            }
        )
    return out


async def team_performance(
    db: AsyncSession,
    *,
    employee_ids: Optional[set[int]] = None,
    on_date: Optional[date] = None,
) -> list[dict]:
    on = on_date or _today()
    job_q = select(FieldJob).where(FieldJob.scheduled_date == on)
    if employee_ids is not None:
        if not employee_ids:
            return []
        job_q = job_q.where(FieldJob.employee_id.in_(employee_ids))
    jobs = (await db.execute(job_q)).scalars().all()

    by_emp: dict[int, dict] = {}
    for j in jobs:
        bucket = by_emp.setdefault(
            j.employee_id,
            {"jobs_assigned": 0, "jobs_completed": 0, "visits_in_progress": 0},
        )
        bucket["jobs_assigned"] += 1
        if j.status == "completed":
            bucket["jobs_completed"] += 1
        elif j.status == "in_progress":
            bucket["visits_in_progress"] += 1

    if not by_emp:
        return []

    emps = (
        await db.execute(select(Employee).where(Employee.id.in_(by_emp.keys())))
    ).scalars().all()

    # Avg visit duration today per employee
    avg_q = (
        select(Visit.employee_id, func.avg(Visit.duration_minutes))
        .where(Visit.employee_id.in_(by_emp.keys()))
        .where(Visit.duration_minutes > 0)
        .group_by(Visit.employee_id)
    )
    avg_rows = (await db.execute(avg_q)).all()
    avg_map = {eid: int(avg or 0) for eid, avg in avg_rows}

    out: list[dict] = []
    for emp in emps:
        bucket = by_emp[emp.id]
        out.append(
            {
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}".strip(),
                "jobs_assigned": bucket["jobs_assigned"],
                "jobs_completed": bucket["jobs_completed"],
                "visits_in_progress": bucket["visits_in_progress"],
                "avg_visit_minutes": avg_map.get(emp.id, 0),
            }
        )
    return out


# ── Field expenses ────────────────────────────────────────────────────
async def create_expense(
    db: AsyncSession,
    *,
    employee: Employee,
    category: str,
    amount: Decimal,
    expense_date: date,
    visit_id: Optional[int] = None,
    receipt_url: Optional[str] = None,
    description: Optional[str] = None,
) -> FieldExpense:
    exp = FieldExpense(
        employee_id=employee.id,
        visit_id=visit_id,
        category=category,
        amount=amount,
        expense_date=expense_date,
        receipt_url=receipt_url,
        description=description,
        status="pending",
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


async def list_expenses_for_employee(
    db: AsyncSession, employee_id: int
) -> Sequence[FieldExpense]:
    return (
        await db.execute(
            select(FieldExpense)
            .where(FieldExpense.employee_id == employee_id)
            .order_by(FieldExpense.expense_date.desc())
        )
    ).scalars().all()

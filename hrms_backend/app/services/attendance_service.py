"""Attendance service: check-in, check-out, summary, regularization."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Attendance,
    AttendanceRegularization,
    Employee,
    Holiday,
    LeaveRequest,
    User,
)
from app.utils.geo import GeoFenceCheck, check_office_geofence


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _get_today_record(
    db: AsyncSession, employee_id: int, on_date: date
) -> Optional[Attendance]:
    return (
        await db.execute(
            select(Attendance)
            .where(Attendance.employee_id == employee_id)
            .where(Attendance.date == on_date)
        )
    ).scalar_one_or_none()


async def check_in(
    db: AsyncSession,
    employee: Employee,
    *,
    lat: float,
    lng: float,
    work_mode: str = "office",
    selfie_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> tuple[Attendance, GeoFenceCheck | None]:
    today = _today()

    existing = await _get_today_record(db, employee.id, today)
    if existing and existing.check_in:
        raise ConflictError("Already checked in today")

    geo: Optional[GeoFenceCheck] = None
    if work_mode == "office":
        from app.services.office_location import get_office_location
        o_lat, o_lng, o_rad = await get_office_location(db)
        geo = check_office_geofence(
            lat,
            lng,
            office_lat=o_lat,
            office_lng=o_lng,
            radius_m=o_rad,
        )
        if not geo.inside:
            raise ValidationError(
                f"Outside office geo-fence ({geo.distance_m}m from office; "
                f"limit {geo.radius_m}m). Use WFH mode if working remotely."
            )
    if work_mode == "wfh" and not selfie_url:
        raise ValidationError("WFH check-in requires a selfie")

    if existing:
        att = existing
    else:
        att = Attendance(
            employee_id=employee.id,
            date=today,
            status="absent",
        )
        db.add(att)

    att.check_in = _now()
    att.check_in_lat = Decimal(str(lat))
    att.check_in_lng = Decimal(str(lng))
    att.check_in_selfie_url = selfie_url
    att.check_in_distance_m = geo.distance_m if geo else None
    att.work_mode = work_mode
    att.source = "gps"
    att.notes = notes
    att.status = "wfh" if work_mode == "wfh" else "present"

    await db.commit()
    await db.refresh(att)
    return att, geo


async def check_out(
    db: AsyncSession,
    employee: Employee,
    *,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> Attendance:
    today = _today()
    att = await _get_today_record(db, employee.id, today)
    if not att or not att.check_in:
        raise ValidationError("No check-in found for today")
    if att.check_out:
        raise ConflictError("Already checked out")

    att.check_out = _now()
    if lat is not None:
        att.check_out_lat = Decimal(str(lat))
    if lng is not None:
        att.check_out_lng = Decimal(str(lng))
    att.total_minutes = int((att.check_out - att.check_in).total_seconds() // 60)
    if att.total_minutes < 240 and att.status == "present":
        att.status = "half_day"
    await db.commit()
    await db.refresh(att)
    return att


async def list_for_employee(
    db: AsyncSession,
    employee_id: int,
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 90,
) -> Sequence[Attendance]:
    stmt = select(Attendance).where(Attendance.employee_id == employee_id)
    if from_date:
        stmt = stmt.where(Attendance.date >= from_date)
    if to_date:
        stmt = stmt.where(Attendance.date <= to_date)
    stmt = stmt.order_by(Attendance.date.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


async def monthly_summary(
    db: AsyncSession,
    employee_id: int,
    *,
    year: int,
    month: int,
) -> dict:
    from calendar import monthrange

    days_in_month = monthrange(year, month)[1]
    first = date(year, month, 1)
    last = date(year, month, days_in_month)

    rows = await list_for_employee(
        db, employee_id, from_date=first, to_date=last, limit=days_in_month
    )
    by_date = {r.date: r for r in rows}

    holidays = (
        await db.execute(
            select(Holiday).where(Holiday.date >= first).where(Holiday.date <= last)
        )
    ).scalars().all()
    holiday_dates = {h.date for h in holidays}

    leaves = (
        await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee_id)
            .where(LeaveRequest.status == "approved")
            .where(LeaveRequest.from_date <= last)
            .where(LeaveRequest.to_date >= first)
        )
    ).scalars().all()
    leave_dates: set[date] = set()
    for lr in leaves:
        d = lr.from_date
        while d <= lr.to_date:
            if first <= d <= last:
                leave_dates.add(d)
            d = d.fromordinal(d.toordinal() + 1)

    days = []
    present = absent = leave_d = holiday_d = wfh_d = 0
    total_minutes = 0
    for i in range(1, days_in_month + 1):
        d = date(year, month, i)
        att = by_date.get(d)
        status = "absent"
        minutes = 0
        work_mode = None
        if d in holiday_dates:
            status, holiday_d = "holiday", holiday_d + 1
        elif d in leave_dates:
            status, leave_d = "leave", leave_d + 1
        elif att:
            status = att.status
            minutes = att.total_minutes
            work_mode = att.work_mode
            if status == "present":
                present += 1
            elif status == "wfh":
                wfh_d += 1
                present += 1
            elif status == "half_day":
                present += 1
            elif status == "absent":
                absent += 1
        else:
            absent += 1
        total_minutes += minutes
        days.append(
            {"date": d, "status": status, "total_minutes": minutes, "work_mode": work_mode}
        )

    counted = max(1, present)
    return {
        "year": year,
        "month": month,
        "days_present": present,
        "days_absent": absent,
        "days_leave": leave_d,
        "days_holiday": holiday_d,
        "days_wfh": wfh_d,
        "total_minutes": total_minutes,
        "avg_minutes": int(total_minutes / counted),
        "days": days,
    }


# ── Regularization ──────────────────────────────────────────────────────
async def request_regularization(
    db: AsyncSession,
    employee: Employee,
    *,
    on_date: date,
    requested_check_in: Optional[datetime],
    requested_check_out: Optional[datetime],
    reason: str,
) -> AttendanceRegularization:
    if not (requested_check_in or requested_check_out):
        raise ValidationError("Provide at least one corrected timestamp")
    reg = AttendanceRegularization(
        employee_id=employee.id,
        date=on_date,
        requested_check_in=requested_check_in,
        requested_check_out=requested_check_out,
        reason=reason,
        status="pending",
    )
    db.add(reg)
    await db.flush()

    from app.services import approval_engine
    await approval_engine.submit_for_approval(
        db,
        request_type="attendance_regularization",
        request_id=reg.id,
        employee_id=employee.id,
        initiated_by=employee.user_id,
        title=f"Regularize {on_date} · {employee.first_name} {employee.last_name}",
        summary=reason,
        request_data={
            "date": str(on_date),
            "requested_check_in": str(requested_check_in)
            if requested_check_in
            else None,
            "requested_check_out": str(requested_check_out)
            if requested_check_out
            else None,
            "employee_code": employee.employee_code,
        },
    )

    await db.commit()
    await db.refresh(reg)
    return reg


async def list_pending_regularizations(
    db: AsyncSession,
) -> Sequence[AttendanceRegularization]:
    return (
        await db.execute(
            select(AttendanceRegularization)
            .where(AttendanceRegularization.status == "pending")
            .order_by(AttendanceRegularization.created_at.desc())
        )
    ).scalars().all()


async def approve_regularization(
    db: AsyncSession,
    reg_id: int,
    *,
    approver: User,
    decision_comment: Optional[str] = None,
) -> AttendanceRegularization:
    reg = (
        await db.execute(
            select(AttendanceRegularization).where(
                AttendanceRegularization.id == reg_id
            )
        )
    ).scalar_one_or_none()
    if not reg:
        raise NotFoundError("Regularization not found")
    if reg.status != "pending":
        raise ValidationError("Already decided")

    att = await _get_today_record(db, reg.employee_id, reg.date)
    if not att:
        att = Attendance(
            employee_id=reg.employee_id,
            date=reg.date,
            status="absent",
            source="admin",
        )
        db.add(att)
    if reg.requested_check_in:
        att.check_in = reg.requested_check_in
    if reg.requested_check_out:
        att.check_out = reg.requested_check_out
    if att.check_in and att.check_out:
        att.total_minutes = int((att.check_out - att.check_in).total_seconds() // 60)
    att.status = "present"
    att.source = "admin"

    reg.status = "approved"
    reg.approver_id = approver.id
    reg.approved_at = _now()
    reg.decision_comment = decision_comment

    from app.services import approval_engine
    await approval_engine.mark_externally_decided(
        db,
        request_type="attendance_regularization",
        request_id=reg.id,
        approve=True,
        decided_by=approver.id,
        comments=decision_comment,
    )

    await db.commit()
    await db.refresh(reg)
    return reg


async def reject_regularization(
    db: AsyncSession,
    reg_id: int,
    *,
    approver: User,
    decision_comment: Optional[str] = None,
) -> AttendanceRegularization:
    reg = (
        await db.execute(
            select(AttendanceRegularization).where(
                AttendanceRegularization.id == reg_id
            )
        )
    ).scalar_one_or_none()
    if not reg:
        raise NotFoundError("Regularization not found")
    if reg.status != "pending":
        raise ValidationError("Already decided")
    reg.status = "rejected"
    reg.approver_id = approver.id
    reg.approved_at = _now()
    reg.decision_comment = decision_comment

    from app.services import approval_engine
    await approval_engine.mark_externally_decided(
        db,
        request_type="attendance_regularization",
        request_id=reg.id,
        approve=False,
        decided_by=approver.id,
        comments=decision_comment,
    )

    await db.commit()
    await db.refresh(reg)
    return reg

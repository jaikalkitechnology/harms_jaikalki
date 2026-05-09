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

    # Guard: if HR/manager has already approved a leave covering today,
    # block the check-in. The employee is on leave; attendance for the
    # day is reflected via the approved leave instead.
    on_leave = (
        await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee.id)
            .where(LeaveRequest.status == "approved")
            .where(LeaveRequest.from_date <= today)
            .where(LeaveRequest.to_date >= today)
            .limit(1)
        )
    ).scalar_one_or_none()
    if on_leave is not None:
        raise ValidationError(
            "You're on approved leave today "
            f"({on_leave.from_date} → {on_leave.to_date}). "
            "Cancel the leave from the Leaves screen if you intend to work."
        )

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

    # Apply late-grace policy: if check-in is past
    # (shift_start + late_grace_minutes), mark the day as half_day.
    from app.services.attendance_policy import apply_late_rule
    await apply_late_rule(db, att, employee.id)

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


# ── Bulk import / CSV upload ────────────────────────────────────────────
_VALID_STATUS = {"present", "absent", "half_day", "wfh", "leave", "holiday"}
_VALID_WORK_MODE = {"office", "wfh", "hybrid", "field"}


def _parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date '{raw}' (use YYYY-MM-DD)")


def _parse_dt(raw: Optional[str], on: date) -> Optional[datetime]:
    """Accept either a full ISO timestamp or a HH:MM(:SS) — combined with `on`."""
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    # Full timestamp first.
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    # Time-only.
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
        try:
            t = datetime.strptime(raw, fmt).time()
            return datetime.combine(on, t)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised time '{raw}' (use HH:MM or ISO 8601)")


async def bulk_import(
    db: AsyncSession,
    rows: list[dict],
) -> dict:
    """Upsert Attendance from a list of pre-parsed dict rows.

    Each row must include `employee_code` and `date`. Optional:
    `status`, `check_in`, `check_out`, `work_mode`, `notes`.

    Status defaults to `present` when check_in is set, else `absent`.
    work_mode defaults to `office`. Existing (employee, date) rows are
    *updated* in place and counted as `rows_updated`.
    """
    # Pre-load employees by code.
    codes = {r.get("employee_code") for r in rows if r.get("employee_code")}
    by_code: dict[str, Employee] = {}
    if codes:
        emps = (
            await db.execute(
                select(Employee).where(Employee.employee_code.in_(codes))
            )
        ).scalars().all()
        by_code = {e.employee_code: e for e in emps}

    errors: list[dict] = []
    rows_imported = 0
    rows_updated = 0
    rows_skipped = 0

    for idx, raw in enumerate(rows, start=2):  # +1 header, +1 1-indexed
        code = (raw.get("employee_code") or "").strip()
        date_raw = (raw.get("date") or "").strip()
        if not code and not date_raw:
            continue  # blank line
        if not code:
            errors.append({"row": idx, "employee_code": None, "date": date_raw,
                           "error": "employee_code is required"})
            rows_skipped += 1
            continue
        if not date_raw:
            errors.append({"row": idx, "employee_code": code, "date": None,
                           "error": "date is required"})
            rows_skipped += 1
            continue
        emp = by_code.get(code)
        if not emp:
            errors.append({"row": idx, "employee_code": code, "date": date_raw,
                           "error": f"unknown employee_code '{code}'"})
            rows_skipped += 1
            continue
        try:
            on = _parse_date(date_raw)
        except ValueError as e:
            errors.append({"row": idx, "employee_code": code, "date": date_raw,
                           "error": str(e)})
            rows_skipped += 1
            continue
        try:
            ci = _parse_dt(raw.get("check_in"), on)
            co = _parse_dt(raw.get("check_out"), on)
        except ValueError as e:
            errors.append({"row": idx, "employee_code": code, "date": date_raw,
                           "error": str(e)})
            rows_skipped += 1
            continue
        if ci and co and co < ci:
            errors.append({"row": idx, "employee_code": code, "date": date_raw,
                           "error": "check_out is before check_in"})
            rows_skipped += 1
            continue

        status = (raw.get("status") or "").strip().lower() or None
        if status and status not in _VALID_STATUS:
            errors.append({"row": idx, "employee_code": code, "date": date_raw,
                           "error": f"invalid status '{status}'"})
            rows_skipped += 1
            continue
        work_mode = (raw.get("work_mode") or "").strip().lower() or None
        if work_mode and work_mode not in _VALID_WORK_MODE:
            errors.append({"row": idx, "employee_code": code, "date": date_raw,
                           "error": f"invalid work_mode '{work_mode}'"})
            rows_skipped += 1
            continue
        notes = (raw.get("notes") or "").strip() or None

        # Default status: present if any timestamp is set; absent otherwise.
        if not status:
            status = "present" if (ci or co) else "absent"
        if not work_mode:
            work_mode = "wfh" if status == "wfh" else "office"

        existing = (
            await db.execute(
                select(Attendance)
                .where(Attendance.employee_id == emp.id)
                .where(Attendance.date == on)
            )
        ).scalar_one_or_none()

        if existing is None:
            att = Attendance(
                employee_id=emp.id,
                date=on,
                status=status,
                work_mode=work_mode,
                source="import",
                check_in=ci,
                check_out=co,
                notes=notes,
            )
            db.add(att)
            rows_imported += 1
        else:
            att = existing
            att.status = status
            att.work_mode = work_mode
            att.source = "import"
            if ci is not None:
                att.check_in = ci
            if co is not None:
                att.check_out = co
            if notes is not None:
                att.notes = notes
            rows_updated += 1

        if att.check_in and att.check_out:
            att.total_minutes = int(
                (att.check_out - att.check_in).total_seconds() // 60
            )
        else:
            att.total_minutes = att.total_minutes or 0

    await db.commit()
    return {
        "rows_total": len(rows),
        "rows_imported": rows_imported,
        "rows_updated": rows_updated,
        "rows_skipped": rows_skipped,
        "errors": errors,
    }


async def calendar_for_employee(
    db: AsyncSession,
    *,
    employee_id: int,
    year: int,
    month: int,
) -> dict:
    """Per-day calendar entries for the (employee, month) pair.
    Sundays and holidays come back marked is_editable=False."""
    from calendar import monthrange
    from datetime import timedelta as _td

    days_in = monthrange(year, month)[1]
    first = date(year, month, 1)
    last = date(year, month, days_in)

    holidays = (
        await db.execute(
            select(Holiday).where(Holiday.date >= first).where(Holiday.date <= last)
        )
    ).scalars().all()
    holiday_by_date = {h.date: h for h in holidays}

    rows = (
        await db.execute(
            select(Attendance)
            .where(Attendance.employee_id == employee_id)
            .where(Attendance.date >= first)
            .where(Attendance.date <= last)
        )
    ).scalars().all()
    by_date = {r.date: r for r in rows}

    leaves = (
        await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee_id)
            .where(LeaveRequest.status == "approved")
            .where(LeaveRequest.from_date <= last)
            .where(LeaveRequest.to_date >= first)
        )
    ).scalars().all()
    leave_by_date: dict[date, LeaveRequest] = {}
    for lr in leaves:
        d = max(lr.from_date, first)
        end = min(lr.to_date, last)
        while d <= end:
            leave_by_date[d] = lr
            d = d + _td(days=1)

    days = []
    counts = dict(
        present=0, absent=0, leave=0, holiday=0, weekoff=0, half_day=0, wfh=0,
    )
    working = 0
    today = _today()

    for i in range(days_in):
        d = first + _td(days=i)
        wd = d.weekday()
        is_sunday = wd == 6
        h = holiday_by_date.get(d)
        att = by_date.get(d)
        leave = leave_by_date.get(d)
        is_future = d > today

        is_editable = not (is_sunday or h is not None or is_future)

        if is_sunday:
            status_ = "week_off"
            counts["weekoff"] += 1
        elif h is not None:
            status_ = "holiday"
            counts["holiday"] += 1
        elif leave is not None:
            status_ = "leave"
            counts["leave"] += 1
        elif att is not None:
            status_ = att.status
            if status_ == "present":
                counts["present"] += 1
            elif status_ == "wfh":
                counts["wfh"] += 1
            elif status_ == "half_day":
                counts["half_day"] += 1
            elif status_ == "absent":
                counts["absent"] += 1
        elif is_future:
            # Don't pre-mark future working days as absent — the
            # calendar should only report what already happened.
            status_ = "upcoming"
        else:
            status_ = "absent"
            counts["absent"] += 1

        if is_editable:
            working += 1

        days.append({
            "date": d,
            "weekday": wd,
            "status": status_,
            "is_sunday": is_sunday,
            "is_holiday": h is not None,
            "holiday_name": h.name if h else None,
            "is_editable": is_editable,
            "attendance_id": att.id if att else None,
            "check_in": att.check_in if att else None,
            "check_out": att.check_out if att else None,
            "work_mode": att.work_mode if att else None,
            "total_minutes": att.total_minutes if att else 0,
            "notes": att.notes if att else None,
            "leave_type": leave.leave_type.code if leave and leave.leave_type else None,
        })

    return {
        "year": year,
        "month": month,
        "employee_id": employee_id,
        "days": days,
        "days_present": counts["present"],
        "days_absent": counts["absent"],
        "days_leave": counts["leave"],
        "days_holiday": counts["holiday"],
        "days_weekoff": counts["weekoff"],
        "days_half_day": counts["half_day"],
        "days_wfh": counts["wfh"],
        "working_days": working,
    }


async def upsert_by_date(
    db: AsyncSession,
    *,
    employee_id: int,
    on_date: date,
    status_: Optional[str],
    check_in: Optional[datetime],
    check_out: Optional[datetime],
    work_mode: Optional[str],
    notes: Optional[str],
    actor_user_id: Optional[int] = None,
) -> Attendance:
    """Admin-side single-day upsert. Refuses Sundays and holidays so
    payroll's working-days denominator stays clean."""
    if on_date.weekday() == 6:
        raise ValidationError(
            "Sunday is a non-working day. Mark the leave from the Leaves "
            "screen if needed instead of overriding attendance."
        )
    is_holiday = (
        await db.execute(
            select(Holiday).where(Holiday.date == on_date).limit(1)
        )
    ).scalar_one_or_none()
    if is_holiday is not None:
        raise ValidationError(
            f"{on_date} is a public holiday ({is_holiday.name}); "
            "attendance updates are blocked."
        )

    if check_in and check_out and check_out < check_in:
        raise ValidationError("check_out is before check_in")

    existing = (
        await db.execute(
            select(Attendance)
            .where(Attendance.employee_id == employee_id)
            .where(Attendance.date == on_date)
        )
    ).scalar_one_or_none()

    if existing is None:
        att = Attendance(
            employee_id=employee_id,
            date=on_date,
            status=status_ or ("present" if (check_in or check_out) else "absent"),
            work_mode=work_mode or "office",
            source="admin",
            check_in=check_in,
            check_out=check_out,
            notes=notes,
        )
        db.add(att)
    else:
        att = existing
        if status_ is not None:
            att.status = status_
        if work_mode is not None:
            att.work_mode = work_mode
        if check_in is not None:
            att.check_in = check_in
        if check_out is not None:
            att.check_out = check_out
        if notes is not None:
            att.notes = notes
        att.source = "admin"

    if att.check_in and att.check_out:
        att.total_minutes = int(
            (att.check_out - att.check_in).total_seconds() // 60
        )

    await db.commit()
    await db.refresh(att)
    return att


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

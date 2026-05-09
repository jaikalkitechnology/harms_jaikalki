from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import User
from app.services.storage import upload_fileobj
from app.schemas.reports import (
    AttendanceStats,
    AttritionStats,
    ComplianceStats,
    DepartmentBreakdown,
    DirectorDashboard,
    HeadcountTrend,
    PayrollCostStats,
    PerformanceStats,
    SalesStats,
    SavedReportCreate,
    SavedReportOut,
    SavedReportUpdate,
    TrainingStats,
    VerificationStats,
)
from app.services import reports_service as reports

router = APIRouter(prefix="/reports", tags=["reports"])


# ─── Standard reports ────────────────────────────────────────────────
@router.get("/headcount", response_model=HeadcountTrend)
async def headcount(
    months: int = Query(default=12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.all")),
):
    return await reports.headcount_trend(db, months=months)


@router.get("/attrition", response_model=AttritionStats)
async def attrition(
    months: int = Query(default=12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.all")),
):
    return await reports.attrition_stats(db, months=months)


@router.get("/department-breakdown", response_model=list[DepartmentBreakdown])
async def department_breakdown(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.team")),
):
    return await reports.department_breakdown(db)


@router.get("/attendance", response_model=AttendanceStats)
async def attendance(
    on_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.team")),
):
    return await reports.attendance_snapshot(db, on_date=on_date)


@router.get("/payroll-cost", response_model=PayrollCostStats)
async def payroll_cost(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.all")),
):
    out = await reports.payroll_cost(db, year=year, month=month)
    if not out:
        raise NotFoundError("No payroll run found for this period")
    return out


@router.get("/compliance", response_model=ComplianceStats)
async def compliance(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.team")),
):
    return await reports.compliance_overview(db)


@router.get("/sales", response_model=SalesStats)
async def sales(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.team")),
):
    return await reports.sales_overview(
        db, period_start=period_start, period_end=period_end
    )


@router.get("/performance", response_model=Optional[PerformanceStats])
async def performance(
    cycle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.all")),
):
    return await reports.performance_overview(db, cycle_id=cycle_id)


@router.get("/verification", response_model=VerificationStats)
async def verification(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.team")),
):
    return await reports.verification_stats(db)


@router.get("/training", response_model=TrainingStats)
async def training(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.team")),
):
    return await reports.training_stats(db)


@router.get("/director-dashboard", response_model=DirectorDashboard)
async def director_dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report.view.all")),
):
    return await reports.director_dashboard(db)


# ─── Saved reports ───────────────────────────────────────────────────
ALLOWED_REPORT_MIME = {
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "image/jpeg",
    "image/png",
}
MAX_REPORT_BYTES = 50 * 1024 * 1024  # 50 MB


@router.get("/saved", response_model=list[SavedReportOut])
async def list_saved(
    search: Optional[str] = None,
    report_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await reports.list_saved_reports(
        db, user_id=user.id, search=search, report_type=report_type
    )


@router.post(
    "/saved",
    response_model=SavedReportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_saved(
    payload: SavedReportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await reports.create_saved_report(
        db, payload=payload.model_dump(), created_by=user.id
    )


@router.put("/saved/{report_id}", response_model=SavedReportOut)
async def update_saved(
    report_id: int,
    payload: SavedReportUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await reports.update_saved_report(
        db,
        report_id,
        user_id=user.id,
        payload=payload.model_dump(exclude_unset=True),
    )


@router.post("/saved/{report_id}/file", response_model=SavedReportOut)
async def upload_report_file(
    report_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Attach a generated artefact (PDF / ZIP / XLSX / CSV / image) to a
    saved report. Replaces any prior attachment."""
    if file.content_type and file.content_type.lower() not in ALLOWED_REPORT_MIME:
        raise ValidationError(f"Unsupported content type: {file.content_type}")
    contents = await file.read()
    if len(contents) > MAX_REPORT_BYTES:
        raise ValidationError("File too large (max 50 MB)")

    import io
    _, url = upload_fileobj(
        io.BytesIO(contents),
        key_prefix=f"reports/{user.id}",
        filename=file.filename or "report.bin",
        content_type=file.content_type,
    )
    return await reports.attach_saved_report_file(
        db,
        report_id,
        user_id=user.id,
        file_url=url,
        file_name=file.filename or "report",
        file_size=len(contents),
        file_mime=file.content_type,
    )


@router.delete(
    "/saved/{report_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_saved(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await reports.delete_saved_report(db, report_id, user_id=user.id)


# ─── Combined attendance + salary export ────────────────────────────
@router.get(
    "/attendance-payroll-export.csv",
    response_class=StreamingResponse,
    summary="One-row-per-employee CSV: attendance summary + computed salary "
    "for the chosen date range.",
)
async def attendance_payroll_export(
    from_date: date = Query(...),
    to_date: date = Query(...),
    employee_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated employee IDs. Omit for all active.",
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("report.view.all")),
):
    from datetime import timedelta
    import csv as _csv
    import io as _io
    from decimal import Decimal

    from sqlalchemy import select
    from app.models import Attendance, Employee, Holiday, SalaryTemplate
    from app.services.salary_calculator import JaikalkiSalaryCalculator

    if from_date > to_date:
        raise NotFoundError("from_date must be on or before to_date")

    ids: list[int] | None = None
    if employee_ids:
        try:
            ids = [int(x) for x in employee_ids.split(",") if x.strip()]
        except ValueError:
            raise NotFoundError("employee_ids must be comma-separated integers")

    emp_stmt = select(Employee).where(Employee.status == "active")
    if ids:
        emp_stmt = emp_stmt.where(Employee.id.in_(ids))
    employees = (await db.execute(emp_stmt)).scalars().all()

    holidays = {
        h.date
        for h in (
            await db.execute(
                select(Holiday)
                .where(Holiday.date >= from_date)
                .where(Holiday.date <= to_date)
            )
        ).scalars().all()
    }

    # Pre-load templates
    template_ids = {e.salary_template_id for e in employees if e.salary_template_id}
    tpls = (
        await db.execute(
            select(SalaryTemplate).where(SalaryTemplate.id.in_(template_ids))
        )
    ).scalars().all() if template_ids else []
    tpl_by_id = {t.id: t for t in tpls}

    # Total calendar + working days in range (Mon-Sat working).
    total_days = (to_date - from_date).days + 1
    working_days_in_range = 0
    d = from_date
    while d <= to_date:
        if d.weekday() != 6 and d not in holidays:
            working_days_in_range += 1
        d = d + timedelta(days=1)

    # Build CSV
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow([
        "employee_code", "name", "category", "designation",
        "from_date", "to_date", "total_days", "working_days_in_range",
        "present", "wfh", "half_day", "absent", "leave",
        "holidays_in_range",
        "ctc_monthly", "gross_monthly", "net_salary_monthly",
        "earned_gross", "earned_net",
    ])

    calc = JaikalkiSalaryCalculator()
    for e in employees:
        rows = (
            await db.execute(
                select(Attendance)
                .where(Attendance.employee_id == e.id)
                .where(Attendance.date >= from_date)
                .where(Attendance.date <= to_date)
            )
        ).scalars().all()
        present = sum(1 for r in rows if r.status == "present")
        wfh = sum(1 for r in rows if r.status == "wfh")
        half = sum(1 for r in rows if r.status == "half_day")
        absent = sum(1 for r in rows if r.status == "absent")
        leave_d = sum(1 for r in rows if r.status == "leave")

        # Effective working days (present + wfh + 0.5*half + paid leave)
        effective = Decimal(present) + Decimal(wfh) + Decimal("0.5") * Decimal(half) + Decimal(leave_d)

        ctc_m = gross_m = net_m = earn_g = earn_n = ""
        if e.salary_template_id and e.salary_template_id in tpl_by_id:
            tpl = tpl_by_id[e.salary_template_id]
            br = calc.calculate(
                tpl, ctc_annual=e.ctc_annual or None, employee=e
            )
            d_ = br.as_dict()
            if not d_.get("is_intern"):
                ctc_m = d_["total_ctc_monthly"]
                gross_m = d_["gross"]
                net_m = d_["net_salary"]
                if working_days_in_range > 0:
                    ratio = float(effective) / working_days_in_range
                    earn_g = round(d_["gross"] * ratio, 2)
                    earn_n = round(d_["net_salary"] * ratio, 2)
                else:
                    earn_g = 0
                    earn_n = 0

        w.writerow([
            e.employee_code,
            f"{e.first_name} {e.last_name}",
            getattr(e, "category_code", "") or "",
            "",  # designation lookup is optional; left blank for speed
            from_date.isoformat(),
            to_date.isoformat(),
            total_days,
            working_days_in_range,
            present,
            wfh,
            half,
            absent,
            leave_d,
            sum(1 for d_ in holidays if from_date <= d_ <= to_date),
            ctc_m, gross_m, net_m, earn_g, earn_n,
        ])

    buf.seek(0)
    filename = f"jaikalki-attendance-payroll-{from_date}-{to_date}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import User
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
@router.get("/saved", response_model=list[SavedReportOut])
async def list_saved(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await reports.list_saved_reports(db, user_id=user.id)


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


@router.delete(
    "/saved/{report_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_saved(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await reports.delete_saved_report(db, report_id, user_id=user.id)

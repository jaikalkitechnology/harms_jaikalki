from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HeadcountPoint(BaseModel):
    period: str  # "2026-04"
    headcount: int
    joined: int
    exited: int


class HeadcountTrend(BaseModel):
    months: int
    points: List[HeadcountPoint]
    current_headcount: int


class AttritionStats(BaseModel):
    period_months: int
    starting_headcount: int
    exits: int
    attrition_pct: float


class DepartmentBreakdown(BaseModel):
    department: str
    headcount: int


class AttendanceStats(BaseModel):
    on_date: date
    present: int
    wfh: int
    leave: int
    absent: int
    holiday: int
    total_employees: int


class PayrollCostStats(BaseModel):
    year: int
    month: int
    total_gross: Decimal
    total_net: Decimal
    total_employer_cost: Decimal
    employee_count: int
    avg_cost_per_employee: Decimal


class ComplianceStats(BaseModel):
    mandatory_courses: int
    employees_total: int
    fully_compliant: int
    partially_compliant: int
    non_compliant: int
    coverage_pct: float


class SalesStats(BaseModel):
    period_start: date
    period_end: date
    leads_count: int
    leads_won: int
    win_rate_pct: float
    quotes_total: Decimal
    orders_total: Decimal


class PerformanceStats(BaseModel):
    cycle_id: int
    cycle_name: str
    self_reviews_submitted: int
    manager_reviews_submitted: int
    pending_self_reviews: int
    pending_manager_reviews: int


class VerificationStats(BaseModel):
    total: int
    completed: int
    in_progress: int
    audit_pending: int
    breach_pct: float
    avg_hours: float


class TrainingStats(BaseModel):
    sessions_total: int
    sessions_completed: int
    upcoming_sessions: int
    total_attendees: int


class DirectorDashboard(BaseModel):
    headcount: HeadcountTrend
    attrition: AttritionStats
    department_breakdown: List[DepartmentBreakdown]
    payroll_this_month: Optional[PayrollCostStats]
    compliance: ComplianceStats
    sales: Optional[SalesStats]
    verification: VerificationStats
    training: TrainingStats


# ── Saved reports ────────────────────────────────────────────────────
class SavedReportCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    report_type: str = Field(
        pattern="^(headcount|attrition|attendance|payroll_cost|compliance|"
        "sales|performance|verification|training|custom)$"
    )
    filters: Optional[dict] = None
    schedule_cron: Optional[str] = None
    schedule_recipients: Optional[List[str]] = None
    is_shared: bool = False


class SavedReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: Optional[str]
    report_type: str
    filters: Optional[dict] = None
    schedule_cron: Optional[str]
    schedule_recipients: Optional[list] = None
    last_run_at: Optional[datetime]
    is_shared: bool
    created_by: Optional[int]

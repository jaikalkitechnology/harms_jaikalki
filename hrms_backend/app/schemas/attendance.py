from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    start_time: time
    end_time: time
    break_duration_min: int
    is_default: bool
    is_active: bool


class AttendanceCheckIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    work_mode: str = Field(default="office", pattern="^(office|wfh|hybrid|field)$")
    selfie_url: Optional[str] = None
    notes: Optional[str] = None


class AttendanceCheckOut(BaseModel):
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)


class AttendanceUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None,
        pattern="^(present|absent|half_day|wfh|leave|holiday)$",
    )
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_mode: Optional[str] = Field(
        default=None, pattern="^(office|wfh|hybrid|field)$"
    )
    notes: Optional[str] = None


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    date: date
    check_in: Optional[datetime]
    check_in_lat: Optional[Decimal]
    check_in_lng: Optional[Decimal]
    check_in_selfie_url: Optional[str]
    check_in_distance_m: Optional[int]
    check_out: Optional[datetime]
    check_out_lat: Optional[Decimal]
    check_out_lng: Optional[Decimal]
    status: str
    work_mode: str
    source: str
    total_minutes: int
    notes: Optional[str]


class AttendanceSummaryDay(BaseModel):
    date: date
    status: str
    total_minutes: int
    work_mode: Optional[str] = None


class AttendanceSummary(BaseModel):
    year: int
    month: int
    days_present: int
    days_absent: int
    days_leave: int
    days_holiday: int
    days_wfh: int
    total_minutes: int
    avg_minutes: int
    days: List[AttendanceSummaryDay]


class RegularizationCreate(BaseModel):
    date: date
    requested_check_in: Optional[datetime] = None
    requested_check_out: Optional[datetime] = None
    reason: str = Field(min_length=5)


class RegularizationDecision(BaseModel):
    decision_comment: Optional[str] = None


class RegularizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    date: date
    requested_check_in: Optional[datetime]
    requested_check_out: Optional[datetime]
    reason: str
    status: str
    approver_id: Optional[int]
    approved_at: Optional[datetime]
    decision_comment: Optional[str]
    created_at: datetime


class AttendanceUploadRowError(BaseModel):
    row: int
    employee_code: Optional[str] = None
    date: Optional[str] = None
    error: str


class AttendanceUploadResult(BaseModel):
    rows_total: int
    rows_imported: int
    rows_updated: int
    rows_skipped: int
    errors: List[AttendanceUploadRowError]


class AttendanceUpsertByDate(BaseModel):
    """Single-day attendance edit by admin from the calendar view."""
    date: date
    status: Optional[str] = Field(
        default=None,
        pattern="^(present|absent|half_day|wfh|leave|holiday)$",
    )
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_mode: Optional[str] = Field(
        default=None, pattern="^(office|wfh|hybrid|field)$"
    )
    notes: Optional[str] = None


class CalendarDay(BaseModel):
    date: date
    weekday: int  # 0 Mon — 6 Sun
    status: str   # present, absent, half_day, wfh, leave, holiday, week_off, blank
    is_sunday: bool
    is_holiday: bool
    holiday_name: Optional[str] = None
    is_editable: bool
    attendance_id: Optional[int] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_mode: Optional[str] = None
    total_minutes: int = 0
    notes: Optional[str] = None
    leave_type: Optional[str] = None


class AttendanceCalendar(BaseModel):
    year: int
    month: int
    employee_id: int
    days: List[CalendarDay]
    days_present: int
    days_absent: int
    days_leave: int
    days_holiday: int
    days_weekoff: int
    days_half_day: int
    days_wfh: int
    working_days: int


class YearMonthSummary(BaseModel):
    month: int
    days_present: int
    days_absent: int
    days_leave: int
    days_holiday: int
    days_weekoff: int
    days_half_day: int
    days_wfh: int
    working_days: int


class AttendanceYearSummary(BaseModel):
    employee_id: int
    year: int
    months: List[YearMonthSummary]
    total_present: int
    total_absent: int
    total_leave: int
    total_holiday: int
    total_weekoff: int
    total_half_day: int
    total_wfh: int
    total_working_days: int

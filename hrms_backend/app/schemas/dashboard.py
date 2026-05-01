from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class TodayAttendance(BaseModel):
    checked_in: bool = False
    checked_out: bool = False
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[str] = None
    work_mode: Optional[str] = None
    distance_m: Optional[int] = None


class LeaveBalanceItem(BaseModel):
    code: str
    name: str
    balance: Decimal


class BirthdayItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    date_of_birth: Optional[date] = None


class ProbationExpiringItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    probation_end_date: date
    days_remaining: int


class TeamMember(BaseModel):
    employee_id: int
    full_name: str
    employee_code: str
    status_today: str  # present / absent / wfh / leave / holiday


class DashboardOut(BaseModel):
    role: Optional[str]
    role_level: int
    user_full_name: str
    employee_id: Optional[int]
    employee_code: Optional[str]
    company_name: str

    # Employee-style widgets (always populated when employee record exists)
    today_attendance: TodayAttendance = TodayAttendance()
    leave_balances: List[LeaveBalanceItem] = []
    next_payday_in_days: Optional[int] = None
    pending_self_leaves: int = 0

    # Manager / HR widgets
    pending_approvals_count: int = 0
    pending_by_type: List[dict] = []

    # Manager-only
    team_size: int = 0
    team_present_today: int = 0
    team_attendance_pct: float = 0.0
    team_today: List[TeamMember] = []

    # HR-only
    birthdays_today: List[BirthdayItem] = []
    probation_expiring_30d: List[ProbationExpiringItem] = []

    # Director-only
    total_headcount: int = 0
    headcount_by_category: List[dict] = []

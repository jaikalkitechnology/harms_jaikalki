from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LeaveTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    days_per_year: Decimal
    carry_forward: bool
    encashable: bool
    requires_attachment_after_days: int
    is_active: bool
    description: Optional[str] = None


class LeaveBalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    leave_type_id: int
    leave_type: Optional[LeaveTypeOut] = None
    year: int
    allocated: Decimal
    used: Decimal
    carried_forward: Decimal
    adjustment: Decimal = Decimal("0")
    balance: Decimal


class LeaveAdjustRequest(BaseModel):
    leave_type_id: int
    delta: Decimal = Field(description="Days to add (+) or remove (−)")
    reason: str = Field(min_length=3, max_length=500)
    year: Optional[int] = None


class LeaveAdjustmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    leave_type_id: int
    year: int
    delta: Decimal
    reason: str
    created_by: Optional[int] = None
    created_at: datetime


class LeaveApplyRequest(BaseModel):
    leave_type_id: int
    from_date: date
    to_date: date
    reason: Optional[str] = None
    half_day: bool = False
    attachment_url: Optional[str] = None


class LeaveDecisionRequest(BaseModel):
    decision_comment: Optional[str] = None


class LeaveRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    leave_type_id: int
    leave_type: Optional[LeaveTypeOut] = None
    from_date: date
    to_date: date
    days: Decimal
    half_day: bool
    reason: Optional[str]
    attachment_url: Optional[str]
    status: str
    applied_at: datetime
    approver_id: Optional[int]
    approved_at: Optional[datetime]
    decision_comment: Optional[str]


class HolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    name: str
    type: str
    is_optional: bool
    location: str


class HolidayCreate(BaseModel):
    date: date
    name: str = Field(min_length=1, max_length=96)
    type: str = Field(default="national", pattern="^(national|regional|company)$")
    is_optional: bool = False
    location: str = "ALL"


class CalendarItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    from_date: date
    to_date: date
    leave_type: str
    days: Decimal
    status: str


class CompOffEarn(BaseModel):
    earned_date: date
    days: Decimal = Field(default=Decimal("1"), gt=0)
    reason: Optional[str] = None


class CompOffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    earned_date: date
    expiry_date: date
    days: Decimal
    status: str
    reason: Optional[str]

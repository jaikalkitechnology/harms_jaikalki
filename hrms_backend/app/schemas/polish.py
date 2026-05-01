from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Assets ──────────────────────────────────────────────────────────
class AssetCreate(BaseModel):
    asset_tag: str
    name: str
    category: str = Field(
        default="other",
        pattern="^(laptop|mobile|headset|monitor|keyboard|mouse|vehicle|other)$",
    )
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    warranty_until: Optional[date] = None
    condition: str = Field(
        default="new", pattern="^(new|good|fair|damaged|retired)$"
    )
    notes: Optional[str] = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_tag: str
    name: str
    category: str
    serial_number: Optional[str]
    purchase_date: Optional[date]
    purchase_cost: Optional[Decimal]
    warranty_until: Optional[date]
    condition: str
    status: str
    assigned_to: Optional[int]
    assigned_at: Optional[datetime]
    notes: Optional[str]


class AssetAssignRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None


class AssetReturnRequest(BaseModel):
    return_condition: str = Field(pattern="^(good|fair|damaged|lost)$")
    notes: Optional[str] = None


class AssetAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    employee_id: int
    assigned_at: datetime
    returned_at: Optional[datetime]
    return_condition: Optional[str]
    notes: Optional[str]


# ─── Visitors ────────────────────────────────────────────────────────
class VisitorCreate(BaseModel):
    full_name: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    company: Optional[str] = None
    purpose: str
    expected_at: datetime


class VisitorCheckIn(BaseModel):
    qr_token: str
    badge_number: Optional[str] = None


class VisitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    contact_phone: Optional[str]
    contact_email: Optional[str]
    company: Optional[str]
    purpose: str
    host_employee_id: int
    expected_at: datetime
    qr_token: str
    checked_in_at: Optional[datetime]
    checked_out_at: Optional[datetime]
    badge_number: Optional[str]
    status: str


# ─── Meeting rooms + bookings ────────────────────────────────────────
class MeetingRoomCreate(BaseModel):
    code: str
    name: str
    location: Optional[str] = None
    capacity: int = Field(default=4, ge=1, le=200)
    has_video: bool = False
    has_whiteboard: bool = True


class MeetingRoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    location: Optional[str]
    capacity: int
    has_video: bool
    has_whiteboard: bool
    is_active: bool


class RoomBookingCreate(BaseModel):
    room_id: int
    title: str
    start_time: datetime
    end_time: datetime
    attendees: Optional[List[str]] = None
    notes: Optional[str] = None


class RoomBookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_id: int
    booked_by_employee_id: int
    title: str
    start_time: datetime
    end_time: datetime
    attendees: Optional[list] = None
    status: str
    notes: Optional[str]


# ─── Job postings + applications ─────────────────────────────────────
class JobPostingCreate(BaseModel):
    code: str
    title: str
    department_id: Optional[int] = None
    location: Optional[str] = None
    employment_type: str = Field(
        default="full_time", pattern="^(full_time|part_time|contract|intern)$"
    )
    description: Optional[str] = None
    requirements: Optional[str] = None
    referral_bonus: Optional[Decimal] = None
    is_internal_only: bool = True
    closes_on: Optional[date] = None


class JobPostingStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|published|closed|filled)$")


class JobPostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    department_id: Optional[int]
    location: Optional[str]
    employment_type: str
    description: Optional[str]
    requirements: Optional[str]
    referral_bonus: Optional[Decimal]
    is_internal_only: bool
    posted_at: datetime
    closes_on: Optional[date]
    status: str


class JobApplicationCreate(BaseModel):
    referrer_employee_id: Optional[int] = None
    cover_note: Optional[str] = None
    resume_url: Optional[str] = None


class JobApplicationStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(submitted|shortlisted|interviewing|offered|hired|rejected|"
        "withdrawn)$"
    )


class JobApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    posting_id: int
    applicant_employee_id: Optional[int]
    external_applicant_name: Optional[str]
    external_applicant_email: Optional[str]
    referrer_employee_id: Optional[int]
    cover_note: Optional[str]
    resume_url: Optional[str]
    status: str
    referral_bonus_paid: bool
    submitted_at: datetime

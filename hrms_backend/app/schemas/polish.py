from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Assets ──────────────────────────────────────────────────────────
_CONDITION = "^(working|damaged|not_working|expired)$"


class AssetSpecField(BaseModel):
    key: Optional[str] = None
    label: str = Field(min_length=1, max_length=60)


class AssetCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    is_accessory: bool
    spec_fields: Optional[list] = None
    sort_order: int
    is_active: bool


class AssetCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=96)
    code: Optional[str] = Field(default=None, max_length=48)
    is_accessory: bool = False
    spec_fields: list[AssetSpecField] = []
    sort_order: Optional[int] = None


class AssetCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=96)
    is_accessory: Optional[bool] = None
    spec_fields: Optional[list[AssetSpecField]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AssetCreate(BaseModel):
    asset_tag: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(default="other", max_length=48)
    brand: Optional[str] = Field(default=None, max_length=80)
    model: Optional[str] = Field(default=None, max_length=120)
    specs: Optional[dict[str, str]] = None
    parent_asset_id: Optional[int] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    warranty_until: Optional[date] = None
    condition: str = Field(default="working", pattern=_CONDITION)
    notes: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=160)
    category: Optional[str] = Field(default=None, max_length=48)
    brand: Optional[str] = Field(default=None, max_length=80)
    model: Optional[str] = Field(default=None, max_length=120)
    specs: Optional[dict[str, str]] = None
    parent_asset_id: Optional[int] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    warranty_until: Optional[date] = None
    condition: Optional[str] = Field(default=None, pattern=_CONDITION)
    # in_stock | in_repair | retired | lost — assignment has its own calls.
    status: Optional[str] = Field(default=None, pattern="^(in_stock|in_repair|retired|lost)$")
    notes: Optional[str] = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_tag: str
    name: str
    category: str
    brand: Optional[str] = None
    model: Optional[str] = None
    specs: Optional[dict] = None
    parent_asset_id: Optional[int] = None
    serial_number: Optional[str]
    purchase_date: Optional[date]
    purchase_cost: Optional[Decimal]
    warranty_until: Optional[date]
    condition: str
    is_usable: bool = True
    status: str
    assigned_to: Optional[int]
    assigned_at: Optional[datetime]
    notes: Optional[str]


class AssetSummaryOut(BaseModel):
    total: int
    in_stock_usable: int
    assigned: int
    not_usable: int
    in_repair: int
    lost: int
    retired: int


class AssetRetireRequest(BaseModel):
    reason: str = Field(pattern="^(expired|damaged|sold|disposed|donated|other)$")
    notes: Optional[str] = Field(default=None, max_length=500)


class AssetAssignRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None
    # Hand over the asset's accessories (e.g. its charger) with it.
    include_accessories: bool = True


class AssetReturnRequest(BaseModel):
    return_condition: str = Field(
        pattern="^(working|damaged|not_working|expired|lost)$"
    )
    notes: Optional[str] = None
    include_accessories: bool = True


class AssetAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    employee_id: int
    assigned_at: datetime
    returned_at: Optional[datetime]
    return_condition: Optional[str]
    notes: Optional[str]
    assigned_by: Optional[int] = None
    received_by: Optional[int] = None


class EmployeeAssetHistoryRow(AssetAssignmentOut):
    asset: AssetOut


class EmployeeAssetsOut(BaseModel):
    current: list[AssetOut]
    history: list[EmployeeAssetHistoryRow]


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


class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[int] = None
    location: Optional[str] = None
    employment_type: Optional[str] = Field(
        default=None, pattern="^(full_time|part_time|contract|intern)$"
    )
    description: Optional[str] = None
    requirements: Optional[str] = None
    referral_bonus: Optional[Decimal] = None
    is_internal_only: Optional[bool] = None
    published_to_app: Optional[bool] = None
    closes_on: Optional[date] = None


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
    published_to_app: bool = False
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

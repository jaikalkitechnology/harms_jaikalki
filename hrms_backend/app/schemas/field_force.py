from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Customer ──────────────────────────────────────────────────────────
class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    type: str = Field(default="lead", pattern="^(lead|prospect|customer|partner)$")
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    geo_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    geo_lng: Optional[float] = Field(default=None, ge=-180, le=180)
    industry: Optional[str] = None
    gst: Optional[str] = None
    pan: Optional[str] = None
    contact_persons: Optional[List[dict]] = None
    territory: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = Field(
        default=None, pattern="^(lead|prospect|customer|partner)$"
    )
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    geo_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    geo_lng: Optional[float] = Field(default=None, ge=-180, le=180)
    industry: Optional[str] = None
    gst: Optional[str] = None
    pan: Optional[str] = None
    contact_persons: Optional[List[dict]] = None
    territory: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    geo_lat: Optional[Decimal]
    geo_lng: Optional[Decimal]
    industry: Optional[str]
    gst: Optional[str]
    pan: Optional[str]
    contact_persons: Optional[List[dict]] = None
    territory: Optional[str]
    is_active: bool


# ─── Field Job ─────────────────────────────────────────────────────────
class FieldJobCreate(BaseModel):
    employee_id: int
    customer_id: int
    job_type: str = Field(
        default="sales_call",
        pattern="^(sales_call|demo|service|delivery|training|collection|survey|other)$",
    )
    scheduled_date: date
    scheduled_time: Optional[str] = Field(default=None, max_length=8)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    notes: Optional[str] = None


class FieldJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    customer_id: int
    job_type: str
    scheduled_date: date
    scheduled_time: Optional[str]
    priority: str
    status: str
    notes: Optional[str]
    assigned_at: datetime
    customer: Optional[CustomerOut] = None


# ─── Visit lifecycle ───────────────────────────────────────────────────
class VisitCheckIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    is_mock: bool = False
    selfie_url: Optional[str] = None


class VisitCheckOut(BaseModel):
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    outcome: Optional[str] = None
    notes: Optional[str] = None
    signature_url: Optional[str] = None


class VisitFormSubmit(BaseModel):
    visit_form: dict


class VisitPhotoCreate(BaseModel):
    photo_url: str
    photo_type: str = Field(
        default="other",
        pattern="^(storefront|shelf|product|document|selfie|other)$",
    )
    geo_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    geo_lng: Optional[float] = Field(default=None, ge=-180, le=180)
    watermarked: bool = False


class VisitPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    visit_id: int
    photo_url: str
    photo_type: str
    geo_lat: Optional[Decimal]
    geo_lng: Optional[Decimal]
    taken_at: datetime
    watermarked: bool


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    employee_id: int
    check_in_time: Optional[datetime]
    check_in_lat: Optional[Decimal]
    check_in_lng: Optional[Decimal]
    check_in_distance_m: Optional[int]
    check_in_selfie_url: Optional[str]
    check_in_is_mock: bool
    check_out_time: Optional[datetime]
    check_out_lat: Optional[Decimal]
    check_out_lng: Optional[Decimal]
    visit_form: Optional[dict] = None
    outcome: Optional[str]
    notes: Optional[str]
    signature_url: Optional[str]
    duration_minutes: int
    photos: List[VisitPhotoOut] = []


# ─── Location tracking ─────────────────────────────────────────────────
class LocationTrackIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: Optional[int] = None
    speed_mps: Optional[float] = None
    heading: Optional[float] = None
    battery_pct: Optional[int] = Field(default=None, ge=0, le=100)
    is_mock: bool = False
    timestamp: Optional[datetime] = None


class LocationTrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    lat: Decimal
    lng: Decimal
    accuracy_m: Optional[int]
    speed_mps: Optional[Decimal]
    heading: Optional[Decimal]
    battery_pct: Optional[int]
    is_mock: bool
    timestamp: datetime


class LiveMapEntry(BaseModel):
    employee_id: int
    employee_code: str
    name: str
    lat: float
    lng: float
    timestamp: datetime
    battery_pct: Optional[int] = None
    current_status: str = "idle"
    last_visit_customer: Optional[str] = None


class TeamPerformanceEntry(BaseModel):
    employee_id: int
    employee_code: str
    name: str
    jobs_assigned: int
    jobs_completed: int
    visits_in_progress: int
    avg_visit_minutes: int


# ─── Field Expense ─────────────────────────────────────────────────────
class FieldExpenseCreate(BaseModel):
    visit_id: Optional[int] = None
    category: str = Field(
        pattern="^(fuel|toll|parking|food|lodging|phone|other)$"
    )
    amount: Decimal = Field(gt=0)
    expense_date: date
    receipt_url: Optional[str] = None
    description: Optional[str] = None


class FieldExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    visit_id: Optional[int]
    category: str
    amount: Decimal
    receipt_url: Optional[str]
    expense_date: date
    description: Optional[str]
    status: str
    approver_id: Optional[int]
    approved_at: Optional[datetime]

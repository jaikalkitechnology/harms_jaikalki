from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Leads ─────────────────────────────────────────────────────────────
class LeadCreate(BaseModel):
    customer_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    source: str = Field(
        default="other",
        pattern="^(website|referral|cold_call|exhibition|campaign|"
        "field_visit|partner|other)$",
    )
    expected_value: Decimal = Field(default=Decimal("0"), ge=0)
    expected_close_date: Optional[date] = None
    assigned_to: Optional[int] = None
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    notes: Optional[str] = None


class LeadStageUpdate(BaseModel):
    stage: str = Field(
        pattern="^(new|contacted|qualified|proposal|negotiation|won|lost)$"
    )
    lost_reason: Optional[str] = None


class LeadUpdate(BaseModel):
    customer_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    source: Optional[str] = Field(
        default=None,
        pattern="^(website|referral|cold_call|exhibition|campaign|"
        "field_visit|partner|other)$",
    )
    expected_value: Optional[Decimal] = Field(default=None, ge=0)
    expected_close_date: Optional[date] = None
    assigned_to: Optional[int] = None
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: Optional[int]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    source: str
    stage: str
    expected_value: Decimal
    expected_close_date: Optional[date]
    assigned_to: Optional[int]
    score: int
    next_action: Optional[str]
    next_action_date: Optional[date]
    notes: Optional[str]
    lost_reason: Optional[str]
    created_at: datetime


# ── Products ──────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Decimal = Field(gt=0)
    tax_pct: Decimal = Field(default=Decimal("18"), ge=0, le=50)
    image_url: Optional[str] = None
    brochure_url: Optional[str] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    unit_price: Decimal
    tax_pct: Decimal
    image_url: Optional[str]
    brochure_url: Optional[str]
    is_active: bool


# ── Quotes / Orders line items ────────────────────────────────────────
class LineItem(BaseModel):
    product_id: int
    name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    tax_pct: Decimal = Field(default=Decimal("18"), ge=0, le=50)


class QuoteCreate(BaseModel):
    customer_id: int
    lead_id: Optional[int] = None
    line_items: List[LineItem]
    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quote_number: str
    customer_id: int
    employee_id: int
    lead_id: Optional[int]
    line_items: list
    subtotal: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    valid_until: Optional[date]
    status: str
    pdf_url: Optional[str]
    signature_url: Optional[str]
    notes: Optional[str]
    created_at: datetime


class QuoteStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|sent|accepted|rejected|expired)$")
    signature_url: Optional[str] = None


# ── Orders ────────────────────────────────────────────────────────────
class OrderCreate(BaseModel):
    customer_id: int
    quote_id: Optional[int] = None
    line_items: List[LineItem]
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_terms: Optional[str] = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    customer_id: int
    employee_id: int
    quote_id: Optional[int]
    line_items: list
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_terms: Optional[str]
    status: str
    tracking_number: Optional[str]
    placed_at: datetime
    delivered_at: Optional[datetime]


class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(pending|confirmed|processing|shipped|delivered|cancelled)$"
    )
    tracking_number: Optional[str] = None


# ── Targets ───────────────────────────────────────────────────────────
class SalesTargetCreate(BaseModel):
    employee_id: int
    period_type: str = Field(default="monthly", pattern="^(monthly|quarterly|yearly)$")
    period_start: date
    period_end: date
    target_amount: Decimal = Field(gt=0)
    commission_pct: Decimal = Field(default=Decimal("2"), ge=0, le=100)
    notes: Optional[str] = None


class SalesTargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    period_type: str
    period_start: date
    period_end: date
    target_amount: Decimal
    achieved_amount: Decimal
    commission_pct: Decimal
    notes: Optional[str]


class SalesTargetSummary(BaseModel):
    target: SalesTargetOut
    achievement_pct: float
    commission_amount: Decimal


# ── Promotions ────────────────────────────────────────────────────────
class PromotionCreate(BaseModel):
    event_name: str
    location: Optional[str] = None
    activity_date: date
    banners_placed: int = 0
    brochures_distributed: int = 0
    demos_given: int = 0
    leads_collected: int = 0
    photos: Optional[List[str]] = None
    notes: Optional[str] = None


class PromotionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    event_name: str
    location: Optional[str]
    activity_date: date
    banners_placed: int
    brochures_distributed: int
    demos_given: int
    leads_collected: int
    photos: Optional[list] = None
    notes: Optional[str]


# ── Pipeline Kanban ──────────────────────────────────────────────────
class PipelineColumn(BaseModel):
    stage: str
    leads: List[LeadOut]
    total_value: Decimal
    count: int

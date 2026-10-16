from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class Lead(Base, TimestampMixin):
    __tablename__ = "sales_leads"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    source: Mapped[str] = mapped_column(
        Enum(
            "website", "referral", "cold_call", "exhibition", "campaign",
            "field_visit", "partner", "other",
            name="lead_source",
        ),
        default="other",
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        Enum(
            "new", "contacted", "qualified", "proposal", "negotiation",
            "won", "lost",
            name="lead_stage",
        ),
        default="new",
        nullable=False,
        index=True,
    )
    expected_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_action_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lost_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Won-approval workflow: when a sales rep flips a lead to "won",
    # status starts as "pending" and waits for an admin (approval.act
    # permission) to approve or reject. Admin transitions are
    # auto-approved.
    won_approval_status: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, index=True
    )
    won_rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    won_requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    won_decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    won_decided_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )


class Opportunity(Base, TimestampMixin):
    __tablename__ = "sales_opportunities"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("sales_leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(
        Enum(
            "discovery", "demo", "proposal", "negotiation", "closed_won",
            "closed_lost",
            name="opportunity_stage",
        ),
        default="discovery",
        nullable=False,
    )
    probability: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    products: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    competitor: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_action_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Product(Base, TimestampMixin):
    __tablename__ = "sales_products"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_product_sku"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("18.00"), nullable=False
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    brochure_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Quote(Base, TimestampMixin):
    __tablename__ = "sales_quotes"
    __table_args__ = (
        UniqueConstraint("quote_number", name="uq_quote_number"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_number: Mapped[str] = mapped_column(String(48), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    lead_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_leads.id", ondelete="SET NULL"), nullable=True
    )
    line_items: Mapped[list] = mapped_column(JSON, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft", "sent", "accepted", "rejected", "expired",
            name="quote_status",
        ),
        default="draft",
        nullable=False,
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"
    __table_args__ = (
        UniqueConstraint("order_number", name="uq_order_number"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(48), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_quotes.id", ondelete="SET NULL"), nullable=True
    )
    line_items: Mapped[list] = mapped_column(JSON, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "confirmed", "processing", "shipped", "delivered",
            "cancelled",
            name="order_status",
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    placed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SalesTarget(Base, TimestampMixin):
    __tablename__ = "sales_targets"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_type: Mapped[str] = mapped_column(
        Enum("monthly", "quarterly", "yearly", name="target_period_type"),
        default="monthly",
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    achieved_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    commission_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("2.00"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # What is counted: sales_amount (₹, the default) or a count of
    # leads_won / new_leads / field_visits / verifications / tasks_done.
    metric: Mapped[str] = mapped_column(
        String(24), default="sales_amount", nullable=False
    )


TARGET_METRICS = (
    "sales_amount",
    "leads_won",
    "new_leads",
    "field_visits",
    "verifications",
    "tasks_done",
)


class PromotionActivity(Base, TimestampMixin):
    __tablename__ = "sales_promotions"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_name: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    banners_placed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    brochures_distributed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    demos_given: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    photos: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ── Lead activity (comments + auto stage transitions) ────────────────
class LeadActivity(Base, TimestampMixin):
    """Append-only timeline entries on a lead — comments from anyone
    with view access, plus auto-logged stage transitions written by
    update_lead_stage()."""

    __tablename__ = "sales_lead_activities"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("sales_leads.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_label: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    activity_type: Mapped[str] = mapped_column(
        Enum(
            "comment", "stage_change", "assignment", "system",
            name="lead_activity_type",
        ),
        default="comment",
        nullable=False,
    )
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    from_stage: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    to_stage: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)

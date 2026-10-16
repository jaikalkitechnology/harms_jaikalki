"""Incentives: schemes HR sets up, monthly (or quarterly) runs that work
out who earned what, the manager review, and the payout through
payroll."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args

PAYOUT_TYPES = ("fixed", "percent_of_achieved")
RUN_STATUSES = ("review", "approved", "cancelled")
LINE_STATUSES = ("pending", "approved", "adjusted", "rejected")


class IncentiveScheme(Base, TimestampMixin):
    """E.g. "Sales incentive": 80 % of target → ₹2,000; 100 % → ₹5,000;
    120 % → ₹8,000 — for confirmed staff with 90 % attendance."""

    __tablename__ = "incentive_schemes"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Which target it pays on (see SalesTarget.metric).
    metric: Mapped[str] = mapped_column(String(24), nullable=False, default="sales_amount")
    period_type: Mapped[str] = mapped_column(String(12), nullable=False, default="monthly")
    # fixed: each slab pays a ₹ amount. percent_of_achieved: each slab
    # pays that % of what was achieved (sales targets).
    payout_type: Mapped[str] = mapped_column(String(24), nullable=False, default="fixed")
    # [{"min_pct": 80, "value": 2000}, …] — the highest slab reached pays.
    slabs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    max_payout: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    # Who it applies to (null = everyone).
    department_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    category_codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    designation_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Eligibility rules (null / false = not checked).
    min_attendance_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exclude_notice: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    no_warning_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_tenure_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class IncentiveRun(Base, TimestampMixin):
    """One scheme for one period: the calculated lines, reviewed by
    managers, approved by HR, paid in a payroll month."""

    __tablename__ = "incentive_runs"
    __table_args__ = (
        UniqueConstraint("scheme_id", "period_start", name="uq_incentive_run_period"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scheme_id: Mapped[int] = mapped_column(
        ForeignKey("incentive_schemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    # Paid with this payroll month.
    payout_year: Mapped[int] = mapped_column(Integer, nullable=False)
    payout_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="review")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class IncentiveLine(Base, TimestampMixin):
    __tablename__ = "incentive_lines"
    __table_args__ = (
        UniqueConstraint("run_id", "employee_id", name="uq_incentive_line"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("incentive_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_targets.id", ondelete="SET NULL"), nullable=True
    )
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    achieved_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    achievement_pct: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    slab_min_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2), nullable=True)
    attendance_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Why not eligible / notes from the calculation.
    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    calculated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    # What will actually be paid (manager / HR may adjust).
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    review_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    review_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_in_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )

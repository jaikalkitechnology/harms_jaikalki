"""Compensation revision (salary increments)."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args


class SalaryRevision(Base, TimestampMixin):
    __tablename__ = "salary_revisions"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(
        Enum(
            "annual_review",
            "promotion",
            "market_correction",
            "retention",
            "role_change",
            "other",
            name="salary_revision_reason",
        ),
        default="annual_review",
        nullable=False,
    )

    previous_ctc_annual: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    new_ctc_annual: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    increment_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False
    )
    new_salary_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("salary_templates.id", ondelete="SET NULL"), nullable=True
    )
    new_designation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("designations.id", ondelete="SET NULL"), nullable=True
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    breakup_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "pending_approval",
            "approved",
            "rejected",
            "applied",
            "cancelled",
            name="salary_revision_status",
        ),
        default="draft",
        nullable=False,
        index=True,
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    increment_letter_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

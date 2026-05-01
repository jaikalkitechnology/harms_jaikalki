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


class ReviewCycle(Base, TimestampMixin):
    __tablename__ = "perf_cycles"
    __table_args__ = (
        UniqueConstraint("code", name="uq_perf_cycle_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    cycle_type: Mapped[str] = mapped_column(
        Enum("quarterly", "half_yearly", "annual", "monthly", name="cycle_type"),
        default="quarterly",
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    self_review_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    manager_review_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    calibration_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "open",
            "review",
            "calibration",
            "closed",
            name="cycle_status",
        ),
        default="draft",
        nullable=False,
        index=True,
    )


class Goal(Base, TimestampMixin):
    __tablename__ = "perf_goals"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cycle_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("perf_cycles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metric: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    target_value: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    weight_pct: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(
            "business",
            "people",
            "growth",
            "operational",
            "personal",
            name="goal_category",
        ),
        default="business",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "active",
            "at_risk",
            "achieved",
            "missed",
            "cancelled",
            name="goal_status",
        ),
        default="draft",
        nullable=False,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class PerformanceReview(Base, TimestampMixin):
    __tablename__ = "perf_reviews"
    __table_args__ = (
        UniqueConstraint(
            "cycle_id", "employee_id", "review_type",
            name="uq_perf_review_cycle_employee_type",
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(
        ForeignKey("perf_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_type: Mapped[str] = mapped_column(
        Enum(
            "self",
            "manager",
            "skip_level",
            "calibrated",
            name="review_type",
        ),
        default="self",
        nullable=False,
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    overall_rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvement_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    increment_recommendation_pct: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    competencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "submitted",
            "calibrated",
            "shared_with_employee",
            "acknowledged",
            name="review_status",
        ),
        default="draft",
        nullable=False,
        index=True,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


class FeedbackRequest(Base, TimestampMixin):
    __tablename__ = "perf_feedback_requests"
    __table_args__ = (
        UniqueConstraint(
            "cycle_id",
            "subject_employee_id",
            "reviewer_employee_id",
            name="uq_feedback_request",
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("perf_cycles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    subject_employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation: Mapped[str] = mapped_column(
        Enum(
            "peer",
            "reportee",
            "manager",
            "cross_functional",
            name="feedback_relation",
        ),
        default="peer",
        nullable=False,
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "submitted", "declined", name="feedback_request_status"
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    requested_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class FeedbackResponse(Base, TimestampMixin):
    __tablename__ = "perf_feedback_responses"
    __table_args__ = (
        UniqueConstraint("request_id", name="uq_feedback_response_request"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("perf_feedback_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvement_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    competencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


class OneOnOneNote(Base, TimestampMixin):
    __tablename__ = "perf_one_on_ones"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    manager_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    agenda: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discussion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    visibility: Mapped[str] = mapped_column(
        Enum(
            "manager_only", "shared", "private", name="one_on_one_visibility"
        ),
        default="shared",
        nullable=False,
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

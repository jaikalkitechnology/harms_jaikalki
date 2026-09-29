from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class LeaveType(Base, TimestampMixin):
    __tablename__ = "leave_types"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    days_per_year: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )
    carry_forward: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_carry_forward: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )
    encashable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_attachment_after_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    # Paid leaves count toward `days_paid` in payroll. Unpaid leave (LWP)
    # is counted as Loss-Of-Pay so the gross is scaled down accordingly.
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # When true, intervening Sundays/holidays sandwiched between two
    # leave days of this type are also counted as leave. The classic
    # case: Friday + Monday LWP → Saturday (off-day at Jaikalki is Sun
    # only, so Sat is a working day already), Sunday between → also LWP.
    applies_sandwich_rule: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Gender eligibility for this leave type — comma-separated codes:
    # "m", "f" (or "m,f" for both, which is the default). Used for
    # maternity / paternity type gating.
    applies_to_genders: Mapped[str] = mapped_column(
        String(16), default="m,f", nullable=False
    )
    # When True the leave is only available to *confirmed* employees.
    # Interns and probationers are blocked from applying, so a fresh
    # joiner can only take sick leave until their confirmation lands.
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )


class LeaveBalance(Base, TimestampMixin):
    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "leave_type_id", "year", name="uq_balance_emp_type_year"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    allocated: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    used: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    carried_forward: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    # Manual HR correction (+/-). Every change is also written to
    # leave_adjustments with a reason for audit.
    adjustment: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )

    leave_type: Mapped["LeaveType"] = relationship(lazy="joined")

    @property
    def balance(self) -> Decimal:
        return (
            (self.allocated or Decimal("0"))
            + (self.carried_forward or Decimal("0"))
            + (self.adjustment or Decimal("0"))
            - (self.used or Decimal("0"))
        )


class LeaveAdjustment(Base, TimestampMixin):
    """Audit trail of manual leave-balance corrections — who added or
    removed how many days of which leave type, for which FY, and why."""

    __tablename__ = "leave_adjustments"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class LeaveRequest(Base, TimestampMixin):
    __tablename__ = "leave_requests"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False
    )
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    half_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "approved",
            "rejected",
            "cancelled",
            name="leave_request_status",
        ),
        default="pending",
        nullable=False,
    )

    applied_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    leave_type: Mapped["LeaveType"] = relationship(lazy="joined")


class Holiday(Base, TimestampMixin):
    __tablename__ = "holidays"
    __table_args__ = (
        UniqueConstraint("date", "location", name="uq_holiday_date_location"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("national", "regional", "company", name="holiday_type"),
        default="national",
        nullable=False,
    )
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location: Mapped[str] = mapped_column(String(64), default="ALL", nullable=False)


class CompOff(Base, TimestampMixin):
    __tablename__ = "comp_off"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    earned_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1"))
    status: Mapped[str] = mapped_column(
        Enum("active", "used", "expired", "rejected", name="comp_off_status"),
        default="active",
        nullable=False,
    )
    used_for_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("leave_requests.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ── Earned-leave accrual ledger (sandwich/auto-accrual policy) ────────
class EarnedLeaveAccrual(Base, TimestampMixin):
    """Idempotent per-(employee, leave_type, year) ledger of leaves
    auto-credited by the earned-leave-accrual policy. Recompute is safe:
    `days_credited` is always set to `floor(present_count / threshold) * credit`
    so re-runs converge on the same number."""

    __tablename__ = "earned_leave_accruals"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "leave_type_id", "year",
            name="uq_earned_accrual_employee_type_year",
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    days_credited: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0"), nullable=False
    )
    last_present_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_recomputed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

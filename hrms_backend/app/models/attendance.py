from datetime import date, datetime, time
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
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class Shift(Base, TimestampMixin):
    __tablename__ = "shifts"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_duration_min: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EmployeeShift(Base, TimestampMixin):
    __tablename__ = "employee_shifts"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    shift: Mapped["Shift"] = relationship(lazy="joined")


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    check_in: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_in_lat: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    check_in_lng: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    check_in_selfie_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    check_in_distance_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_out_lat: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    check_out_lng: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "present",
            "absent",
            "half_day",
            "wfh",
            "leave",
            "holiday",
            name="attendance_status",
        ),
        default="absent",
        nullable=False,
    )
    work_mode: Mapped[str] = mapped_column(
        Enum("office", "wfh", "hybrid", "field", name="attendance_work_mode"),
        default="office",
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        Enum("gps", "manual", "admin", "import", name="attendance_source"),
        default="gps",
        nullable=False,
    )
    total_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AttendanceRegularization(Base, TimestampMixin):
    __tablename__ = "attendance_regularizations"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_check_in: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    requested_check_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="regularization_status"),
        default="pending",
        nullable=False,
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

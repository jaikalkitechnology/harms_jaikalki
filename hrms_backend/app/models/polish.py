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
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args


# ─── Asset Management ────────────────────────────────────────────────
class Asset(Base, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("asset_tag", name="uq_asset_tag"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(
            "laptop",
            "mobile",
            "headset",
            "monitor",
            "keyboard",
            "mouse",
            "vehicle",
            "other",
            name="asset_category",
        ),
        default="other",
        nullable=False,
    )
    serial_number: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    purchase_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    warranty_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    condition: Mapped[str] = mapped_column(
        Enum("new", "good", "fair", "damaged", "retired", name="asset_condition"),
        default="new",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "in_stock",
            "assigned",
            "in_repair",
            "lost",
            "retired",
            name="asset_status",
        ),
        default="in_stock",
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AssetAssignment(Base, TimestampMixin):
    __tablename__ = "asset_assignments"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    return_condition: Mapped[Optional[str]] = mapped_column(
        Enum("good", "fair", "damaged", "lost", name="asset_return_condition"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


# ─── Visitor Management ──────────────────────────────────────────────
class Visitor(Base, TimestampMixin):
    __tablename__ = "visitors"
    __table_args__ = (
        UniqueConstraint("qr_token", name="uq_visitor_qr"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    host_employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    qr_token: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    checked_out_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    badge_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "scheduled",
            "checked_in",
            "checked_out",
            "no_show",
            "cancelled",
            name="visitor_status",
        ),
        default="scheduled",
        nullable=False,
        index=True,
    )


# ─── Meeting Room Booking ────────────────────────────────────────────
class MeetingRoom(Base, TimestampMixin):
    __tablename__ = "meeting_rooms"
    __table_args__ = (
        UniqueConstraint("code", name="uq_meeting_room_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    has_video: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_whiteboard: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RoomBooking(Base, TimestampMixin):
    __tablename__ = "meeting_room_bookings"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("meeting_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booked_by_employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    attendees: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "booked", "in_progress", "completed", "cancelled",
            name="room_booking_status",
        ),
        default="booked",
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ─── Internal Job Postings + Referrals ──────────────────────────────
class JobPosting(Base, TimestampMixin):
    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint("code", name="uq_job_posting_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    employment_type: Mapped[str] = mapped_column(
        Enum(
            "full_time", "part_time", "contract", "intern",
            name="job_employment_type",
        ),
        default="full_time",
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referral_bonus: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    is_internal_only: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    posted_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    posted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    closes_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft", "published", "closed", "filled",
            name="job_posting_status",
        ),
        default="draft",
        nullable=False,
        index=True,
    )


class JobApplication(Base, TimestampMixin):
    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint(
            "posting_id", "applicant_employee_id",
            name="uq_application_posting_applicant",
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    external_applicant_name: Mapped[Optional[str]] = mapped_column(
        String(160), nullable=True
    )
    external_applicant_email: Mapped[Optional[str]] = mapped_column(
        String(160), nullable=True
    )
    referrer_employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cover_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "submitted",
            "shortlisted",
            "interviewing",
            "offered",
            "hired",
            "rejected",
            "withdrawn",
            name="job_application_status",
        ),
        default="submitted",
        nullable=False,
        index=True,
    )
    referral_bonus_paid: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

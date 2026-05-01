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


class FieldEmployee(Base, TimestampMixin):
    __tablename__ = "field_employees"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_field_employee_employee_id"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        Enum("sales", "service", "delivery", "trainer", "other", name="field_type"),
        default="sales",
        nullable=False,
    )
    territory: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    vehicle_type: Mapped[Optional[str]] = mapped_column(
        Enum("two_wheeler", "four_wheeler", "public_transport", "walk", name="vehicle_type"),
        nullable=True,
    )
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    current_status: Mapped[str] = mapped_column(
        Enum("idle", "on_visit", "in_transit", "off_duty", name="field_employee_status"),
        default="idle",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    type: Mapped[str] = mapped_column(
        Enum("lead", "prospect", "customer", "partner", name="customer_type"),
        default="lead",
        nullable=False,
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    geo_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    geo_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    gst: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    contact_persons: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    territory: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class FieldJob(Base, TimestampMixin):
    __tablename__ = "field_jobs"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(
        Enum(
            "sales_call",
            "demo",
            "service",
            "delivery",
            "training",
            "collection",
            "survey",
            "other",
            name="field_job_type",
        ),
        default="sales_call",
        nullable=False,
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "urgent", name="field_job_priority"),
        default="medium",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "scheduled",
            "in_progress",
            "completed",
            "cancelled",
            "skipped",
            name="field_job_status",
        ),
        default="scheduled",
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    customer: Mapped["Customer"] = relationship(lazy="joined")
    visit: Mapped[Optional["Visit"]] = relationship(
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )


class Visit(Base, TimestampMixin):
    __tablename__ = "field_visits"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_visit_job"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("field_jobs.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )

    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_in_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    check_in_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    check_in_distance_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    check_in_selfie_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    check_in_is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_out_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    check_out_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)

    visit_form: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    job: Mapped["FieldJob"] = relationship(back_populates="visit")
    photos: Mapped[List["VisitPhoto"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class VisitPhoto(Base, TimestampMixin):
    __tablename__ = "field_visit_photos"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id: Mapped[int] = mapped_column(
        ForeignKey("field_visits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    photo_type: Mapped[str] = mapped_column(
        Enum("storefront", "shelf", "product", "document", "selfie", "other",
             name="visit_photo_type"),
        default="other",
        nullable=False,
    )
    geo_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    geo_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    taken_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    watermarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    visit: Mapped["Visit"] = relationship(back_populates="photos")


class LocationTrack(Base):
    __tablename__ = "field_location_tracks"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    accuracy_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    speed_mps: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    heading: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    battery_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )


class FieldExpense(Base, TimestampMixin):
    __tablename__ = "field_expenses"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    visit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("field_visits.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(
        Enum(
            "fuel",
            "toll",
            "parking",
            "food",
            "lodging",
            "phone",
            "other",
            name="field_expense_category",
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", "reimbursed",
             name="field_expense_status"),
        default="pending",
        nullable=False,
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

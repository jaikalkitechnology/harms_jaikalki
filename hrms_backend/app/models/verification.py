from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class VerificationTemplate(Base, TimestampMixin):
    """Configurable JSON-driven verification template (no-code)."""

    __tablename__ = "verification_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_verification_template_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum(
            "address",
            "employment",
            "document",
            "business",
            "education",
            "criminal",
            "bank",
            "other",
            name="verification_type",
        ),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fields: Mapped[list] = mapped_column(JSON, nullable=False)
    photo_requirements: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    signature_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    sla_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Verification(Base, TimestampMixin):
    """A verification job assigned to a field employee."""

    __tablename__ = "verifications"
    __table_args__ = (
        UniqueConstraint("ticket_number", name="uq_verification_ticket"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(String(48), nullable=False)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("verification_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        Enum(
            "address",
            "employment",
            "document",
            "business",
            "education",
            "criminal",
            "bank",
            "other",
            name="verification_type",
        ),
        nullable=False,
    )
    subject_name: Mapped[str] = mapped_column(String(160), nullable=False)
    subject_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    requested_by_org: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    assigned_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "in_progress",
            "submitted",
            "audit_pending",
            "audit_passed",
            "audit_failed",
            "completed",
            "cancelled",
            name="verification_status",
        ),
        default="pending",
        nullable=False,
        index=True,
    )

    # Submission data
    form_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    photos: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    geo_lat: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    geo_lng: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Result
    result: Mapped[Optional[str]] = mapped_column(
        Enum(
            "positive", "negative", "unable_to_verify", "partial",
            name="verification_result",
        ),
        nullable=True,
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Audit
    audited_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    audit_status: Mapped[Optional[str]] = mapped_column(
        Enum("approved", "rejected", "rework", name="verification_audit_status"),
        nullable=True,
    )
    audit_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fraud_flags: Mapped[list["VerificationFraudFlag"]] = relationship(
        back_populates="verification",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class VerificationFraudFlag(Base, TimestampMixin):
    __tablename__ = "verification_fraud_flags"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_id: Mapped[int] = mapped_column(
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flag_type: Mapped[str] = mapped_column(
        Enum(
            "duplicate_subject",
            "geo_anomaly",
            "photo_tampered",
            "form_inconsistent",
            "missing_documents",
            "suspicious_pattern",
            "other",
            name="fraud_flag_type",
        ),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="fraud_flag_severity"),
        default="medium",
        nullable=False,
    )
    detected_by: Mapped[str] = mapped_column(
        Enum("system", "auditor", name="fraud_flag_detector"),
        default="system",
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    verification: Mapped["Verification"] = relationship(back_populates="fraud_flags")

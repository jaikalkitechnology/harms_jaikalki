from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
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


COMPLAINT_TYPES = (
    "sexual_harassment",  # POSH-only
    "fraud",
    "manager_issue",
    "hr_issue",
    "director_issue",
    "safety",
    "discrimination",
    "general",
)

PRIVACY_LEVELS = ("anonymous", "confidential", "open")
SEVERITY = ("low", "medium", "high", "critical")
STATUS = (
    "submitted",
    "acknowledged",
    "under_investigation",
    "action_taken",
    "resolved",
    "withdrawn",
    "rejected",
)


class JusticeComplaint(Base, TimestampMixin):
    __tablename__ = "justice_complaints"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(
        String(48), unique=True, nullable=False, index=True
    )

    complaint_type: Mapped[str] = mapped_column(
        Enum(*COMPLAINT_TYPES, name="justice_complaint_type"), nullable=False
    )
    privacy_level: Mapped[str] = mapped_column(
        Enum(*PRIVACY_LEVELS, name="justice_privacy_level"),
        default="confidential",
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        Enum(*SEVERITY, name="justice_severity"),
        default="medium",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(*STATUS, name="justice_status"),
        default="submitted",
        nullable=False,
        index=True,
    )

    # Encrypted fields. We store ciphertext + a hash so we can de-duplicate
    # / search without revealing the plaintext.
    complainant_id_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Also keep a *non-encrypted* employee_id ONLY when privacy_level is
    # 'open' (the complainant explicitly opts in). Routing services must
    # check privacy_level before using this.
    complainant_employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    desired_outcome_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    incident_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    assigned_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    evidence: Mapped[List["JusticeEvidence"]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    accused: Mapped[List["JusticeAccused"]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    witnesses: Mapped[List["JusticeWitness"]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    actions: Mapped[List["JusticeAction"]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="JusticeAction.action_date",
    )
    timeline: Mapped[List["JusticeTimeline"]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="JusticeTimeline.event_date",
    )


class JusticeEvidence(Base, TimestampMixin):
    __tablename__ = "justice_evidence"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    complaint: Mapped["JusticeComplaint"] = relationship(back_populates="evidence")


class JusticeAccused(Base, TimestampMixin):
    __tablename__ = "justice_accused"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accused_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    accused_employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    relationship_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    complaint: Mapped["JusticeComplaint"] = relationship(back_populates="accused")


class JusticeWitness(Base, TimestampMixin):
    __tablename__ = "justice_witnesses"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    witness_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    witness_statement_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    complaint: Mapped["JusticeComplaint"] = relationship(back_populates="witnesses")


class JusticeAction(Base, TimestampMixin):
    __tablename__ = "justice_actions"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        Enum(
            "acknowledged",
            "assigned",
            "investigation_started",
            "comment",
            "warning_issued",
            "training_assigned",
            "transfer",
            "termination",
            "case_closed",
            "no_action",
            name="justice_action_type",
        ),
        nullable=False,
    )
    action_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    taken_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    complaint: Mapped["JusticeComplaint"] = relationship(back_populates="actions")


class JusticeTimeline(Base, TimestampMixin):
    __tablename__ = "justice_timeline"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    done_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    complaint: Mapped["JusticeComplaint"] = relationship(back_populates="timeline")


class JusticeAccessLog(Base):
    __tablename__ = "justice_access_log"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(48), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class IccMember(Base, TimestampMixin):
    __tablename__ = "icc_members"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_name: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[str] = mapped_column(
        Enum(
            "presiding_officer",
            "member",
            "external_member",
            "secretary",
            name="icc_role",
        ),
        nullable=False,
    )
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    term_start: Mapped[date] = mapped_column(Date, nullable=False)
    term_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class RetaliationFlag(Base, TimestampMixin):
    __tablename__ = "retaliation_flags"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("justice_complaints.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flag_type: Mapped[str] = mapped_column(String(48), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    detected_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PoshAnnualReport(Base, TimestampMixin):
    __tablename__ = "posh_annual_reports"
    __table_args__ = (
        UniqueConstraint("year", name="uq_posh_annual_report_year"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_complaints: Mapped[int] = mapped_column(Integer, default=0)
    resolved: Mapped[int] = mapped_column(Integer, default=0)
    pending: Mapped[int] = mapped_column(Integer, default=0)
    actions_taken_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    generated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

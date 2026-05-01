"""Phase 19 launch-readiness models — notifications, audit log, resignation,
password reset OTP, MFA-related tables."""
from datetime import date, datetime
from typing import Optional

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
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args


# ─── Notifications ───────────────────────────────────────────────────
class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(
        Enum("in_app", "email", "push", name="notification_channel"),
        default="in_app",
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "sent", "failed", "read",
            name="notification_status",
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class DeviceToken(Base, TimestampMixin):
    __tablename__ = "device_tokens"
    __table_args__ = (
        UniqueConstraint("token", name="uq_device_token"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(
        Enum("android", "ios", "web", name="device_platform"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


# ─── Audit log ───────────────────────────────────────────────────────
class AuditLog(Base):
    """Append-only audit trail. Captured by middleware + explicit logger."""

    __tablename__ = "audit_logs"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_label: Mapped[Optional[str]] = mapped_column(
        String(160), nullable=True
    )
    action: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )


# ─── Resignation / offboarding ───────────────────────────────────────
class Resignation(Base, TimestampMixin):
    __tablename__ = "resignations"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_resignation_employee_open"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    proposed_last_working_day: Mapped[date] = mapped_column(Date, nullable=False)
    actual_last_working_day: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "submitted",
            "manager_review",
            "accepted",
            "rejected",
            "in_notice",
            "ndc_pending",
            "cleared",
            "settled",
            "cancelled",
            name="resignation_status",
        ),
        default="submitted",
        nullable=False,
        index=True,
    )
    manager_decision_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    manager_decision_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    manager_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notice_period_days: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )
    ndc_checklist: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hr_cleared_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    final_settlement_amount: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    final_settled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    exit_interview_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )


# ─── Password reset OTP ──────────────────────────────────────────────
class PasswordResetOtp(Base, TimestampMixin):
    __tablename__ = "password_reset_otps"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


# ─── MFA backup codes ────────────────────────────────────────────────
class MfaBackupCode(Base, TimestampMixin):
    __tablename__ = "mfa_backup_codes"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

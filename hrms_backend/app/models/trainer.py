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


class TrainerProfile(Base, TimestampMixin):
    __tablename__ = "trainer_profiles"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_trainer_employee"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=True
    )
    is_external: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    profile_photo_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    languages: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    specializations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    years_experience: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    rating_average: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=0, nullable=False
    )
    sessions_completed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TrainingSession(Base, TimestampMixin):
    __tablename__ = "trainer_sessions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_training_session_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainer_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lms_courses.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    session_type: Mapped[str] = mapped_column(
        Enum(
            "in_person",
            "virtual",
            "hybrid",
            "self_paced",
            name="training_session_type",
        ),
        default="virtual",
        nullable=False,
    )
    scheduled_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timezone: Mapped[str] = mapped_column(String(48), default="Asia/Kolkata", nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    qr_token: Mapped[Optional[str]] = mapped_column(
        String(96), nullable=True, index=True
    )
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "scheduled",
            "open_for_registration",
            "in_progress",
            "completed",
            "cancelled",
            name="training_session_status",
        ),
        default="scheduled",
        nullable=False,
        index=True,
    )

    participants: Mapped[List["SessionParticipant"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SessionParticipant(Base, TimestampMixin):
    __tablename__ = "trainer_session_participants"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "employee_id", name="uq_session_participant"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("trainer_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "registered",
            "attended",
            "no_show",
            "completed",
            "cancelled",
            name="session_participant_status",
        ),
        default="registered",
        nullable=False,
    )

    session: Mapped["TrainingSession"] = relationship(back_populates="participants")


class TrainerReview(Base, TimestampMixin):
    __tablename__ = "trainer_reviews"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "employee_id", name="uq_trainer_review"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("trainer_sessions.id", ondelete="SET NULL"), nullable=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

from datetime import date, datetime, time
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
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class DwpTemplate(Base, TimestampMixin):
    __tablename__ = "dwp_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_dwp_template_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    # 'morning' (start-of-day plan) or 'eod' (end-of-day summary)
    type: Mapped[str] = mapped_column(
        Enum("morning", "eod", name="dwp_template_type"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fields: Mapped[List["DwpTemplateField"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DwpTemplateField.display_order",
    )


class DwpTemplateField(Base, TimestampMixin):
    __tablename__ = "dwp_template_fields"
    __table_args__ = (
        UniqueConstraint(
            "template_id", "key", name="uq_dwp_template_field_key"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("dwp_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(48), nullable=False)
    label: Mapped[str] = mapped_column(String(96), nullable=False)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # text, textarea, number, percent, rating, select, multi_select, tasks,
    # photo_url, voice_url
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    template: Mapped["DwpTemplate"] = relationship(back_populates="fields")


class DwpSubmission(Base, TimestampMixin):
    __tablename__ = "dwp_submissions"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "date", "type", name="uq_dwp_submission_per_day"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[int] = mapped_column(
        ForeignKey("dwp_templates.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        Enum("morning", "eod", name="dwp_submission_type"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    total_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    mood_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    linked_morning_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dwp_submissions.id", ondelete="SET NULL"),
        nullable=True,
    )

    fields: Mapped[List["DwpSubmissionField"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    comments: Mapped[List["DwpComment"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DwpComment.created_at",
    )
    template: Mapped["DwpTemplate"] = relationship(lazy="joined")


class DwpSubmissionField(Base):
    __tablename__ = "dwp_submission_fields"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("dwp_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_key: Mapped[str] = mapped_column(String(48), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    submission: Mapped["DwpSubmission"] = relationship(back_populates="fields")


class DwpComment(Base, TimestampMixin):
    __tablename__ = "dwp_comments"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("dwp_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commented_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_kudos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    submission: Mapped["DwpSubmission"] = relationship(back_populates="comments")


class DwpReminderSetting(Base, TimestampMixin):
    __tablename__ = "dwp_reminder_settings"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=True
    )
    morning_reminder_at: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    eod_reminder_at: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    late_alert_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DwpTag(Base, TimestampMixin):
    __tablename__ = "dwp_tags"
    __table_args__ = (
        UniqueConstraint("code", name="uq_dwp_tag_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#F4B71F", nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

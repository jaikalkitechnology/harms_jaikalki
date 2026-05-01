from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class Course(Base, TimestampMixin):
    __tablename__ = "lms_courses"
    __table_args__ = (
        UniqueConstraint("code", name="uq_course_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        Enum(
            "onboarding",
            "compliance",
            "technical",
            "leadership",
            "soft_skills",
            "product",
            "other",
            name="course_category",
        ),
        default="other",
        nullable=False,
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    difficulty: Mapped[str] = mapped_column(
        Enum("beginner", "intermediate", "advanced", name="course_difficulty"),
        default="beginner",
        nullable=False,
    )
    estimated_hours: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validity_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    modules: Mapped[List["CourseModule"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseModule.sort_order",
        lazy="selectin",
    )


class CourseModule(Base, TimestampMixin):
    __tablename__ = "lms_modules"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("lms_courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="modules")
    lessons: Mapped[List["CourseLesson"]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="CourseLesson.sort_order",
        lazy="selectin",
    )


class CourseLesson(Base, TimestampMixin):
    __tablename__ = "lms_lessons"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("lms_modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(
        Enum(
            "video",
            "pdf",
            "article",
            "external_link",
            "image",
            "audio",
            "quiz",
            "scorm",
            "live_session",
            name="lesson_content_type",
        ),
        default="article",
        nullable=False,
    )
    content_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    article_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    module: Mapped["CourseModule"] = relationship(back_populates="lessons")


class CourseEnrollment(Base, TimestampMixin):
    __tablename__ = "lms_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "course_id", name="uq_enrollment_employee_course"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("lms_courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "enrolled",
            "in_progress",
            "completed",
            "expired",
            "dropped",
            name="enrollment_status",
        ),
        default="enrolled",
        nullable=False,
        index=True,
    )
    progress_percentage: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    progress: Mapped[List["LessonProgress"]] = relationship(
        back_populates="enrollment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LessonProgress(Base, TimestampMixin):
    __tablename__ = "lms_lesson_progress"
    __table_args__ = (
        UniqueConstraint(
            "enrollment_id", "lesson_id", name="uq_lesson_progress"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("lms_enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lms_lessons.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("not_started", "in_progress", "completed", name="lesson_progress_status"),
        default="not_started",
        nullable=False,
    )
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    enrollment: Mapped["CourseEnrollment"] = relationship(back_populates="progress")


class Badge(Base, TimestampMixin):
    __tablename__ = "lms_badges"
    __table_args__ = (
        UniqueConstraint("code", name="uq_badge_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    points_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    courses_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_days_required: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    tier: Mapped[str] = mapped_column(
        Enum("bronze", "silver", "gold", "platinum", name="badge_tier"),
        default="bronze",
        nullable=False,
    )


class EmployeeBadge(Base, TimestampMixin):
    __tablename__ = "lms_employee_badges"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "badge_id", name="uq_employee_badge"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id: Mapped[int] = mapped_column(
        ForeignKey("lms_badges.id", ondelete="CASCADE"), nullable=False
    )
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


class EmployeeLearningStat(Base, TimestampMixin):
    """Aggregate per-employee gamification stats."""

    __tablename__ = "lms_employee_stats"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_lms_stat_employee"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    courses_completed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    lessons_completed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    level: Mapped[str] = mapped_column(
        Enum("bronze", "silver", "gold", "platinum", name="learning_level"),
        default="bronze",
        nullable=False,
    )

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
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class QuestionBank(Base, TimestampMixin):
    __tablename__ = "exam_questions"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        Enum(
            "single_choice",
            "multiple_choice",
            "true_false",
            "fill_blank",
            "match_pairs",
            "short_answer",
            name="question_type",
        ),
        default="single_choice",
        nullable=False,
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(
        Enum("easy", "medium", "hard", name="question_difficulty"),
        default="medium",
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    marks: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    time_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "retired", name="question_status"),
        default="active",
        nullable=False,
    )

    options: Mapped[List["QuestionOption"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.sort_order",
        lazy="selectin",
    )


class QuestionOption(Base, TimestampMixin):
    __tablename__ = "exam_question_options"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("exam_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["QuestionBank"] = relationship(back_populates="options")


class Exam(Base, TimestampMixin):
    __tablename__ = "exam_exams"
    __table_args__ = (
        UniqueConstraint("code", name="uq_exam_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lms_courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    exam_type: Mapped[str] = mapped_column(
        Enum(
            "practice", "assessment", "certification", "mandatory", name="exam_type"
        ),
        default="assessment",
        nullable=False,
    )
    total_questions: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    time_limit_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    passing_percentage: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )
    question_selection: Mapped[str] = mapped_column(
        Enum("fixed", "random", name="exam_question_selection"),
        default="fixed",
        nullable=False,
    )
    shuffle_questions: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    shuffle_options: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    attempts_allowed: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    cooldown_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    negative_marking: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    anti_cheat_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validity_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    questions: Mapped[List["ExamQuestion"]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="ExamQuestion.sort_order",
        lazy="selectin",
    )


class ExamQuestion(Base, TimestampMixin):
    __tablename__ = "exam_exam_questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", name="uq_exam_question"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exam_exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False
    )
    marks_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exam: Mapped["Exam"] = relationship(back_populates="questions")


class ExamAttempt(Base, TimestampMixin):
    __tablename__ = "exam_attempts"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exam_exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_taken_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    percentage: Mapped[Numeric] = mapped_column(
        Numeric(5, 2), default=0, nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "in_progress",
            "submitted",
            "auto_submitted",
            "abandoned",
            "invalidated",
            name="attempt_status",
        ),
        default="in_progress",
        nullable=False,
        index=True,
    )
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cheating_flags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    question_order: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    answers: Mapped[List["AttemptAnswer"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AttemptAnswer(Base, TimestampMixin):
    __tablename__ = "exam_attempt_answers"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id", "question_id", name="uq_attempt_answer"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    text_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    marks_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_taken_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    attempt: Mapped["ExamAttempt"] = relationship(back_populates="answers")


class Certificate(Base, TimestampMixin):
    __tablename__ = "exam_certificates"
    __table_args__ = (
        UniqueConstraint("certificate_number", name="uq_certificate_number"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    certificate_number: Mapped[str] = mapped_column(String(64), nullable=False)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lms_courses.id", ondelete="SET NULL"), nullable=True
    )
    exam_attempt_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exam_attempts.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    score_percentage: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

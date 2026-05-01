"""Examination system: question bank, exams, attempts, certificates

Revision ID: 20260501_0012
Revises: 20260501_0011
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0012"
down_revision: Union[str, None] = "20260501_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "exam_questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column(
            "question_type",
            sa.Enum(
                "single_choice",
                "multiple_choice",
                "true_false",
                "fill_blank",
                "match_pairs",
                "short_answer",
                name="question_type",
            ),
            nullable=False,
            server_default="single_choice",
        ),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column(
            "difficulty",
            sa.Enum("easy", "medium", "hard", name="question_difficulty"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("marks", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("time_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "retired", name="question_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_exam_questions_department_id", "exam_questions", ["department_id"]
    )
    op.create_index("ix_exam_questions_topic", "exam_questions", ["topic"])

    op.create_table(
        "exam_question_options",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("exam_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column(
            "is_correct", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_exam_question_options_question_id",
        "exam_question_options",
        ["question_id"],
    )

    op.create_table(
        "exam_exams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("lms_courses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "exam_type",
            sa.Enum(
                "practice",
                "assessment",
                "certification",
                "mandatory",
                name="exam_type",
            ),
            nullable=False,
            server_default="assessment",
        ),
        sa.Column(
            "total_questions", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column(
            "time_limit_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column(
            "passing_percentage",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column(
            "question_selection",
            sa.Enum("fixed", "random", name="exam_question_selection"),
            nullable=False,
            server_default="fixed",
        ),
        sa.Column(
            "shuffle_questions",
            sa.Boolean(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "shuffle_options", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column(
            "attempts_allowed", sa.Integer(), nullable=False, server_default="3"
        ),
        sa.Column(
            "cooldown_hours", sa.Integer(), nullable=False, server_default="24"
        ),
        sa.Column(
            "negative_marking", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("anti_cheat_settings", sa.JSON(), nullable=True),
        sa.Column("validity_months", sa.Integer(), nullable=True),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_exam_code"),
        **_TABLE_KW,
    )
    op.create_index("ix_exam_exams_course_id", "exam_exams", ["course_id"])

    op.create_table(
        "exam_exam_questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "exam_id",
            sa.Integer(),
            sa.ForeignKey("exam_exams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("exam_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("marks_override", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("exam_id", "question_id", name="uq_exam_question"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_exam_exam_questions_exam_id", "exam_exam_questions", ["exam_id"]
    )

    op.create_table(
        "exam_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "exam_id",
            sa.Integer(),
            sa.ForeignKey("exam_exams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column(
            "time_taken_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "percentage", sa.Numeric(5, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            sa.Enum(
                "in_progress",
                "submitted",
                "auto_submitted",
                "abandoned",
                "invalidated",
                name="attempt_status",
            ),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "attempt_number", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column("ip_address", sa.String(48), nullable=True),
        sa.Column("device_info", sa.String(500), nullable=True),
        sa.Column("cheating_flags", sa.JSON(), nullable=True),
        sa.Column("question_order", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_exam_attempts_exam_id", "exam_attempts", ["exam_id"])
    op.create_index(
        "ix_exam_attempts_employee_id", "exam_attempts", ["employee_id"]
    )
    op.create_index("ix_exam_attempts_status", "exam_attempts", ["status"])

    op.create_table(
        "exam_attempt_answers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "attempt_id",
            sa.Integer(),
            sa.ForeignKey("exam_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("exam_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selected_option_ids", sa.JSON(), nullable=True),
        sa.Column("text_answer", sa.Text(), nullable=True),
        sa.Column(
            "is_correct", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column(
            "marks_awarded", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "time_taken_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "attempt_id", "question_id", name="uq_attempt_answer"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_exam_attempt_answers_attempt_id",
        "exam_attempt_answers",
        ["attempt_id"],
    )

    op.create_table(
        "exam_certificates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("certificate_number", sa.String(64), nullable=False),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("lms_courses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "exam_attempt_id",
            sa.Integer(),
            sa.ForeignKey("exam_attempts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("issued_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("score_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("revoked_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "certificate_number", name="uq_certificate_number"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_exam_certificates_employee_id",
        "exam_certificates",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_table("exam_certificates")
    op.drop_table("exam_attempt_answers")
    op.drop_table("exam_attempts")
    op.drop_table("exam_exam_questions")
    op.drop_table("exam_exams")
    op.drop_table("exam_question_options")
    op.drop_table("exam_questions")

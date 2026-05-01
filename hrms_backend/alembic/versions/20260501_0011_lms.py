"""LMS: courses, modules, lessons, enrollments, progress, gamification

Revision ID: 20260501_0011
Revises: 20260501_0010
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0011"
down_revision: Union[str, None] = "20260501_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "lms_courses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "onboarding",
                "compliance",
                "technical",
                "leadership",
                "soft_skills",
                "product",
                "other",
                name="course_category",
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "difficulty",
            sa.Enum(
                "beginner", "intermediate", "advanced", name="course_difficulty"
            ),
            nullable=False,
            server_default="beginner",
        ),
        sa.Column(
            "estimated_hours", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column(
            "is_mandatory", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("validity_months", sa.Integer(), nullable=True),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("points", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_course_code"),
        **_TABLE_KW,
    )

    op.create_table(
        "lms_modules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("lms_courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_lms_modules_course_id", "lms_modules", ["course_id"])

    op.create_table(
        "lms_lessons",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "module_id",
            sa.Integer(),
            sa.ForeignKey("lms_modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum(
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
            nullable=False,
            server_default="article",
        ),
        sa.Column("content_url", sa.String(500), nullable=True),
        sa.Column("article_body", sa.Text(), nullable=True),
        sa.Column(
            "duration_minutes", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_lms_lessons_module_id", "lms_lessons", ["module_id"])

    op.create_table(
        "lms_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("lms_courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("enrolled_at", sa.DateTime(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "enrolled",
                "in_progress",
                "completed",
                "expired",
                "dropped",
                name="enrollment_status",
            ),
            nullable=False,
            server_default="enrolled",
        ),
        sa.Column(
            "progress_percentage",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "employee_id", "course_id", name="uq_enrollment_employee_course"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_lms_enrollments_employee_id", "lms_enrollments", ["employee_id"]
    )
    op.create_index(
        "ix_lms_enrollments_course_id", "lms_enrollments", ["course_id"]
    )
    op.create_index("ix_lms_enrollments_status", "lms_enrollments", ["status"])

    op.create_table(
        "lms_lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "enrollment_id",
            sa.Integer(),
            sa.ForeignKey("lms_enrollments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lesson_id",
            sa.Integer(),
            sa.ForeignKey("lms_lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "not_started", "in_progress", "completed",
                name="lesson_progress_status",
            ),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column(
            "time_spent_seconds", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "enrollment_id", "lesson_id", name="uq_lesson_progress"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_lms_lesson_progress_enrollment_id",
        "lms_lesson_progress",
        ["enrollment_id"],
    )

    op.create_table(
        "lms_badges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(48), nullable=True),
        sa.Column(
            "points_required", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "courses_required", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "streak_days_required",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "tier",
            sa.Enum("bronze", "silver", "gold", "platinum", name="badge_tier"),
            nullable=False,
            server_default="bronze",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_badge_code"),
        **_TABLE_KW,
    )

    op.create_table(
        "lms_employee_badges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "badge_id",
            sa.Integer(),
            sa.ForeignKey("lms_badges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("awarded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("employee_id", "badge_id", name="uq_employee_badge"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_lms_employee_badges_employee_id",
        "lms_employee_badges",
        ["employee_id"],
    )

    op.create_table(
        "lms_employee_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "courses_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "lessons_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
        sa.Column(
            "level",
            sa.Enum(
                "bronze", "silver", "gold", "platinum", name="learning_level"
            ),
            nullable=False,
            server_default="bronze",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("employee_id", name="uq_lms_stat_employee"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_lms_employee_stats_employee_id",
        "lms_employee_stats",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_table("lms_employee_stats")
    op.drop_table("lms_employee_badges")
    op.drop_table("lms_badges")
    op.drop_table("lms_lesson_progress")
    op.drop_table("lms_enrollments")
    op.drop_table("lms_lessons")
    op.drop_table("lms_modules")
    op.drop_table("lms_courses")

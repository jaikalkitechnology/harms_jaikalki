"""Trainer department: profiles, sessions, participants, reviews

Revision ID: 20260501_0013
Revises: 20260501_0012
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0013"
down_revision: Union[str, None] = "20260501_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "trainer_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "is_external", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("headline", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(160), nullable=True),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("profile_photo_url", sa.String(500), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("specializations", sa.JSON(), nullable=True),
        sa.Column(
            "years_experience", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "rating_average", sa.Numeric(3, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "sessions_completed",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("employee_id", name="uq_trainer_employee"),
        **_TABLE_KW,
    )

    op.create_table(
        "trainer_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "trainer_id",
            sa.Integer(),
            sa.ForeignKey("trainer_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
            "session_type",
            sa.Enum(
                "in_person",
                "virtual",
                "hybrid",
                "self_paced",
                name="training_session_type",
            ),
            nullable=False,
            server_default="virtual",
        ),
        sa.Column("scheduled_start", sa.DateTime(), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(), nullable=False),
        sa.Column(
            "timezone",
            sa.String(48),
            nullable=False,
            server_default="Asia/Kolkata",
        ),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("meeting_url", sa.String(500), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("qr_token", sa.String(96), nullable=True),
        sa.Column("recording_url", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "open_for_registration",
                "in_progress",
                "completed",
                "cancelled",
                name="training_session_status",
            ),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_training_session_code"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_trainer_sessions_trainer_id", "trainer_sessions", ["trainer_id"]
    )
    op.create_index("ix_trainer_sessions_status", "trainer_sessions", ["status"])
    op.create_index("ix_trainer_sessions_qr_token", "trainer_sessions", ["qr_token"])

    op.create_table(
        "trainer_session_participants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("trainer_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "registered",
                "attended",
                "no_show",
                "completed",
                "cancelled",
                name="session_participant_status",
            ),
            nullable=False,
            server_default="registered",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "session_id", "employee_id", name="uq_session_participant"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_trainer_session_participants_session_id",
        "trainer_session_participants",
        ["session_id"],
    )
    op.create_index(
        "ix_trainer_session_participants_employee_id",
        "trainer_session_participants",
        ["employee_id"],
    )

    op.create_table(
        "trainer_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "trainer_id",
            sa.Integer(),
            sa.ForeignKey("trainer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("trainer_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column(
            "is_anonymous", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "session_id", "employee_id", name="uq_trainer_review"
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_trainer_reviews_trainer_id", "trainer_reviews", ["trainer_id"]
    )


def downgrade() -> None:
    op.drop_table("trainer_reviews")
    op.drop_table("trainer_session_participants")
    op.drop_table("trainer_sessions")
    op.drop_table("trainer_profiles")

"""Performance management: cycles, goals, reviews, feedback, 1-on-1s

Revision ID: 20260501_0014
Revises: 20260501_0013
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0014"
down_revision: Union[str, None] = "20260501_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "perf_cycles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column(
            "cycle_type",
            sa.Enum(
                "quarterly", "half_yearly", "annual", "monthly",
                name="cycle_type",
            ),
            nullable=False,
            server_default="quarterly",
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("self_review_due", sa.Date(), nullable=True),
        sa.Column("manager_review_due", sa.Date(), nullable=True),
        sa.Column("calibration_due", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "open", "review", "calibration", "closed",
                name="cycle_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_perf_cycle_code"),
        **_TABLE_KW,
    )
    op.create_index("ix_perf_cycles_status", "perf_cycles", ["status"])

    op.create_table(
        "perf_goals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            sa.Integer(),
            sa.ForeignKey("perf_cycles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metric", sa.String(120), nullable=True),
        sa.Column("target_value", sa.String(120), nullable=True),
        sa.Column("weight_pct", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "category",
            sa.Enum(
                "business", "people", "growth", "operational", "personal",
                name="goal_category",
            ),
            nullable=False,
            server_default="business",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "active", "at_risk", "achieved", "missed", "cancelled",
                name="goal_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_perf_goals_employee_id", "perf_goals", ["employee_id"])
    op.create_index("ix_perf_goals_cycle_id", "perf_goals", ["cycle_id"])
    op.create_index("ix_perf_goals_status", "perf_goals", ["status"])

    op.create_table(
        "perf_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "cycle_id",
            sa.Integer(),
            sa.ForeignKey("perf_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "review_type",
            sa.Enum(
                "self", "manager", "skip_level", "calibrated",
                name="review_type",
            ),
            nullable=False,
            server_default="self",
        ),
        sa.Column(
            "reviewer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("overall_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("achievements", sa.Text(), nullable=True),
        sa.Column("improvement_areas", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("increment_recommendation_pct", sa.Integer(), nullable=True),
        sa.Column("competencies", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "submitted",
                "calibrated",
                "shared_with_employee",
                "acknowledged",
                name="review_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "cycle_id",
            "employee_id",
            "review_type",
            name="uq_perf_review_cycle_employee_type",
        ),
        **_TABLE_KW,
    )
    op.create_index("ix_perf_reviews_cycle_id", "perf_reviews", ["cycle_id"])
    op.create_index(
        "ix_perf_reviews_employee_id", "perf_reviews", ["employee_id"]
    )
    op.create_index("ix_perf_reviews_status", "perf_reviews", ["status"])

    op.create_table(
        "perf_feedback_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "cycle_id",
            sa.Integer(),
            sa.ForeignKey("perf_cycles.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "subject_employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "relation",
            sa.Enum(
                "peer",
                "reportee",
                "manager",
                "cross_functional",
                name="feedback_relation",
            ),
            nullable=False,
            server_default="peer",
        ),
        sa.Column(
            "is_anonymous", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "submitted", "declined",
                name="feedback_request_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "requested_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "cycle_id",
            "subject_employee_id",
            "reviewer_employee_id",
            name="uq_feedback_request",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_perf_feedback_requests_cycle_id",
        "perf_feedback_requests",
        ["cycle_id"],
    )
    op.create_index(
        "ix_perf_feedback_requests_subject_employee_id",
        "perf_feedback_requests",
        ["subject_employee_id"],
    )
    op.create_index(
        "ix_perf_feedback_requests_reviewer_employee_id",
        "perf_feedback_requests",
        ["reviewer_employee_id"],
    )
    op.create_index(
        "ix_perf_feedback_requests_status",
        "perf_feedback_requests",
        ["status"],
    )

    op.create_table(
        "perf_feedback_responses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("perf_feedback_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("improvement_areas", sa.Text(), nullable=True),
        sa.Column("competencies", sa.JSON(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("request_id", name="uq_feedback_response_request"),
        **_TABLE_KW,
    )

    op.create_table(
        "perf_one_on_ones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "manager_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("agenda", sa.Text(), nullable=True),
        sa.Column("discussion_notes", sa.Text(), nullable=True),
        sa.Column("action_items", sa.JSON(), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum(
                "manager_only", "shared", "private",
                name="one_on_one_visibility",
            ),
            nullable=False,
            server_default="shared",
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_perf_one_on_ones_employee_id",
        "perf_one_on_ones",
        ["employee_id"],
    )
    op.create_index(
        "ix_perf_one_on_ones_manager_id",
        "perf_one_on_ones",
        ["manager_id"],
    )


def downgrade() -> None:
    op.drop_table("perf_one_on_ones")
    op.drop_table("perf_feedback_responses")
    op.drop_table("perf_feedback_requests")
    op.drop_table("perf_reviews")
    op.drop_table("perf_goals")
    op.drop_table("perf_cycles")

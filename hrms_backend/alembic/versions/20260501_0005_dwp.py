"""Daily Work Planning (DWP) module

Revision ID: 20260501_0005
Revises: 20260501_0004
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0005"
down_revision: Union[str, None] = "20260501_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "dwp_templates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "department_id",
            sa.Integer,
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "type",
            sa.Enum("morning", "eod", name="dwp_template_type"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_dwp_template_code"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "dwp_template_fields",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "template_id",
            sa.Integer,
            sa.ForeignKey("dwp_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(48), nullable=False),
        sa.Column("label", sa.String(96), nullable=False),
        sa.Column("help_text", sa.Text),
        sa.Column("field_type", sa.String(32), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("options", sa.JSON, nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("template_id", "key", name="uq_dwp_template_field_key"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_dwp_template_fields_template_id",
        "dwp_template_fields",
        ["template_id"],
    )

    op.create_table(
        "dwp_submissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            sa.Integer,
            sa.ForeignKey("dwp_templates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum("morning", "eod", name="dwp_submission_type"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("submitted_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("total_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("mood_rating", sa.Integer, nullable=True),
        sa.Column(
            "linked_morning_id",
            sa.Integer,
            sa.ForeignKey("dwp_submissions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "employee_id", "date", "type", name="uq_dwp_submission_per_day"
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_dwp_submissions_employee_id", "dwp_submissions", ["employee_id"])
    op.create_index("ix_dwp_submissions_date", "dwp_submissions", ["date"])

    op.create_table(
        "dwp_submission_fields",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "submission_id",
            sa.Integer,
            sa.ForeignKey("dwp_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_key", sa.String(48), nullable=False),
        sa.Column("value", sa.Text),
        sa.Column("file_url", sa.String(500), nullable=True),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_dwp_submission_fields_submission_id",
        "dwp_submission_fields",
        ["submission_id"],
    )

    op.create_table(
        "dwp_comments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "submission_id",
            sa.Integer,
            sa.ForeignKey("dwp_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "commented_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text, nullable=False),
        sa.Column("is_kudos", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_dwp_comments_submission_id", "dwp_comments", ["submission_id"]
    )

    op.create_table(
        "dwp_reminder_settings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "department_id",
            sa.Integer,
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("morning_reminder_at", sa.Time, nullable=True),
        sa.Column("eod_reminder_at", sa.Time, nullable=True),
        sa.Column("late_alert_minutes", sa.Integer, nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "dwp_tags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("color", sa.String(16), nullable=False, server_default="#F4B71F"),
        sa.Column(
            "department_id",
            sa.Integer,
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_dwp_tag_code"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )


def downgrade() -> None:
    op.drop_table("dwp_tags")
    op.drop_table("dwp_reminder_settings")
    op.drop_index("ix_dwp_comments_submission_id", table_name="dwp_comments")
    op.drop_table("dwp_comments")
    op.drop_index(
        "ix_dwp_submission_fields_submission_id",
        table_name="dwp_submission_fields",
    )
    op.drop_table("dwp_submission_fields")
    op.drop_index("ix_dwp_submissions_date", table_name="dwp_submissions")
    op.drop_index("ix_dwp_submissions_employee_id", table_name="dwp_submissions")
    op.drop_table("dwp_submissions")
    op.drop_index(
        "ix_dwp_template_fields_template_id",
        table_name="dwp_template_fields",
    )
    op.drop_table("dwp_template_fields")
    op.drop_table("dwp_templates")

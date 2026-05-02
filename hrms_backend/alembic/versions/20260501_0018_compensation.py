"""Compensation: salary revisions

Revision ID: 20260501_0018
Revises: 20260501_0017
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0018"
down_revision: Union[str, None] = "20260501_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "salary_revisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "proposed_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reason",
            sa.Enum(
                "annual_review",
                "promotion",
                "market_correction",
                "retention",
                "role_change",
                "other",
                name="salary_revision_reason",
            ),
            nullable=False,
            server_default="annual_review",
        ),
        sa.Column("previous_ctc_annual", sa.Numeric(12, 2), nullable=False),
        sa.Column("new_ctc_annual", sa.Numeric(12, 2), nullable=False),
        sa.Column("increment_pct", sa.Numeric(6, 3), nullable=False),
        sa.Column(
            "new_salary_template_id",
            sa.Integer(),
            sa.ForeignKey("salary_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "new_designation_id",
            sa.Integer(),
            sa.ForeignKey("designations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("breakup_snapshot", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_approval",
                "approved",
                "rejected",
                "applied",
                "cancelled",
                name="salary_revision_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "approved_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("increment_letter_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_salary_revisions_employee_id",
        "salary_revisions",
        ["employee_id"],
    )
    op.create_index(
        "ix_salary_revisions_status", "salary_revisions", ["status"]
    )


def downgrade() -> None:
    op.drop_table("salary_revisions")

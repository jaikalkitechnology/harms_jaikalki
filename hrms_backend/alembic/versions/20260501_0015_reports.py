"""Reports & analytics: saved report definitions

Revision ID: 20260501_0015
Revises: 20260501_0014
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0015"
down_revision: Union[str, None] = "20260501_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "report_saved",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "report_type",
            sa.Enum(
                "headcount",
                "attrition",
                "attendance",
                "payroll_cost",
                "compliance",
                "sales",
                "performance",
                "verification",
                "training",
                "custom",
                name="report_type",
            ),
            nullable=False,
            server_default="custom",
        ),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("schedule_cron", sa.String(48), nullable=True),
        sa.Column("schedule_recipients", sa.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_saved_report_code"),
        **_TABLE_KW,
    )


def downgrade() -> None:
    op.drop_table("report_saved")

"""Universal approval engine

Revision ID: 20260501_0004
Revises: 20260501_0003
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0004"
down_revision: Union[str, None] = "20260501_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(48), nullable=False, unique=True),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("levels_config", sa.JSON, nullable=False),
        sa.Column("conditions_json", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("request_type", sa.String(48), nullable=False),
        sa.Column("request_id", sa.Integer, nullable=False),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("request_data", sa.JSON, nullable=False),
        sa.Column("title", sa.String(160), nullable=False, server_default=""),
        sa.Column("summary", sa.Text),
        sa.Column("current_level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("max_levels", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", "cancelled", "escalated",
                name="approval_status",
            ),
            nullable=False, server_default="pending",
        ),
        sa.Column(
            "initiated_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("initiated_at", sa.DateTime, nullable=False),
        sa.Column("final_status", sa.String(16), nullable=True),
        sa.Column("final_decision_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("request_type", "request_id", name="uq_approval_request"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_approvals_request_type", "approvals", ["request_type"])
    op.create_index("ix_approvals_request_id", "approvals", ["request_id"])
    op.create_index("ix_approvals_employee_id", "approvals", ["employee_id"])
    op.create_index("ix_approvals_status", "approvals", ["status"])

    op.create_table(
        "approval_actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "approval_id",
            sa.Integer,
            sa.ForeignKey("approvals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "approver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "approved", "rejected", "delegated", "commented", "cancelled",
                name="approval_action_kind",
            ),
            nullable=False,
        ),
        sa.Column("comments", sa.Text),
        sa.Column(
            "delegated_to",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_at", sa.DateTime, nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_approval_actions_approval_id", "approval_actions", ["approval_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_approval_actions_approval_id", table_name="approval_actions"
    )
    op.drop_table("approval_actions")
    op.drop_index("ix_approvals_status", table_name="approvals")
    op.drop_index("ix_approvals_employee_id", table_name="approvals")
    op.drop_index("ix_approvals_request_id", table_name="approvals")
    op.drop_index("ix_approvals_request_type", table_name="approvals")
    op.drop_table("approvals")
    op.drop_table("approval_workflows")

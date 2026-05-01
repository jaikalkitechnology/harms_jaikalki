"""Phase 19 launch readiness: notifications, device tokens, audit log,
resignation, password reset OTP, MFA backup codes

Revision ID: 20260501_0017
Revises: 20260501_0016
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0017"
down_revision: Union[str, None] = "20260501_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    # Notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum("in_app", "email", "push", name="notification_channel"),
            nullable=False,
            server_default="in_app",
        ),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "sent", "failed", "read",
                name="notification_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_status", "notifications", ["status"])

    # Device tokens
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "platform",
            sa.Enum("android", "ios", "web", name="device_platform"),
            nullable=False,
        ),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("token", name="uq_device_token"),
        **_TABLE_KW,
    )
    op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])

    # Audit log
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_label", sa.String(160), nullable=True),
        sa.Column("action", sa.String(96), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("method", sa.String(8), nullable=True),
        sa.Column("path", sa.String(255), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index(
        "ix_audit_logs_entity_type", "audit_logs", ["entity_type"]
    )
    op.create_index(
        "ix_audit_logs_entity_id", "audit_logs", ["entity_id"]
    )
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])

    # Resignations
    op.create_table(
        "resignations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("proposed_last_working_day", sa.Date(), nullable=False),
        sa.Column("actual_last_working_day", sa.Date(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "submitted",
                "manager_review",
                "accepted",
                "rejected",
                "in_notice",
                "ndc_pending",
                "cleared",
                "settled",
                "cancelled",
                name="resignation_status",
            ),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("manager_decision_at", sa.DateTime(), nullable=True),
        sa.Column(
            "manager_decision_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("manager_comment", sa.Text(), nullable=True),
        sa.Column(
            "notice_period_days", sa.Integer(), nullable=False, server_default="60"
        ),
        sa.Column("ndc_checklist", sa.JSON(), nullable=True),
        sa.Column("hr_cleared_at", sa.DateTime(), nullable=True),
        sa.Column("final_settlement_amount", sa.Integer(), nullable=True),
        sa.Column("final_settled_at", sa.DateTime(), nullable=True),
        sa.Column("exit_interview_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("employee_id", name="uq_resignation_employee_open"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_resignations_employee_id", "resignations", ["employee_id"]
    )
    op.create_index("ix_resignations_status", "resignations", ["status"])

    # Password reset OTP
    op.create_table(
        "password_reset_otps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("otp_hash", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_password_reset_otps_email", "password_reset_otps", ["email"]
    )

    # MFA backup codes
    op.create_table(
        "mfa_backup_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_mfa_backup_codes_user_id", "mfa_backup_codes", ["user_id"]
    )


def downgrade() -> None:
    op.drop_table("mfa_backup_codes")
    op.drop_table("password_reset_otps")
    op.drop_table("resignations")
    op.drop_table("audit_logs")
    op.drop_table("device_tokens")
    op.drop_table("notifications")

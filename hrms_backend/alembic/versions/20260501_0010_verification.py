"""Verification field force: templates, jobs, fraud flags, audit

Revision ID: 20260501_0010
Revises: 20260501_0009
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0010"
down_revision: Union[str, None] = "20260501_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}

_VERIFICATION_TYPE = sa.Enum(
    "address",
    "employment",
    "document",
    "business",
    "education",
    "criminal",
    "bank",
    "other",
    name="verification_type",
)


def upgrade() -> None:
    op.create_table(
        "verification_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("type", _VERIFICATION_TYPE, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("photo_requirements", sa.JSON(), nullable=True),
        sa.Column(
            "signature_required", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("sla_hours", sa.Integer(), nullable=False, server_default="48"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_verification_template_code"),
        **_TABLE_KW,
    )

    op.create_table(
        "verifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticket_number", sa.String(48), nullable=False),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("verification_templates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("type", _VERIFICATION_TYPE, nullable=False),
        sa.Column("subject_name", sa.String(160), nullable=False),
        sa.Column("subject_data", sa.JSON(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("requested_by_org", sa.String(160), nullable=True),
        sa.Column(
            "assigned_to",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "submitted",
                "audit_pending",
                "audit_passed",
                "audit_failed",
                "completed",
                "cancelled",
                name="verification_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("form_data", sa.JSON(), nullable=True),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("signature_url", sa.String(500), nullable=True),
        sa.Column("geo_lat", sa.String(32), nullable=True),
        sa.Column("geo_lng", sa.String(32), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column(
            "result",
            sa.Enum(
                "positive", "negative", "unable_to_verify", "partial",
                name="verification_result",
            ),
            nullable=True,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("report_pdf_url", sa.String(500), nullable=True),
        sa.Column(
            "audited_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("audited_at", sa.DateTime(), nullable=True),
        sa.Column(
            "audit_status",
            sa.Enum(
                "approved", "rejected", "rework",
                name="verification_audit_status",
            ),
            nullable=True,
        ),
        sa.Column("audit_comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("ticket_number", name="uq_verification_ticket"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_verifications_template_id", "verifications", ["template_id"]
    )
    op.create_index(
        "ix_verifications_assigned_to", "verifications", ["assigned_to"]
    )
    op.create_index("ix_verifications_status", "verifications", ["status"])

    op.create_table(
        "verification_fraud_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "verification_id",
            sa.Integer(),
            sa.ForeignKey("verifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "flag_type",
            sa.Enum(
                "duplicate_subject",
                "geo_anomaly",
                "photo_tampered",
                "form_inconsistent",
                "missing_documents",
                "suspicious_pattern",
                "other",
                name="fraud_flag_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", "critical", name="fraud_flag_severity"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "detected_by",
            sa.Enum("system", "auditor", name="fraud_flag_detector"),
            nullable=False,
            server_default="system",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_verification_fraud_flags_verification_id",
        "verification_fraud_flags",
        ["verification_id"],
    )


def downgrade() -> None:
    op.drop_table("verification_fraud_flags")
    op.drop_table("verifications")
    op.drop_table("verification_templates")

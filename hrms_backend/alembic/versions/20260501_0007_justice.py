"""Justice Portal: complaints, evidence, ICC, audit log, POSH

Revision ID: 20260501_0007
Revises: 20260501_0006
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0007"
down_revision: Union[str, None] = "20260501_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


COMPLAINT_TYPES = (
    "sexual_harassment", "fraud", "manager_issue", "hr_issue",
    "director_issue", "safety", "discrimination", "general",
)
PRIVACY = ("anonymous", "confidential", "open")
SEVERITY = ("low", "medium", "high", "critical")
STATUS = (
    "submitted", "acknowledged", "under_investigation",
    "action_taken", "resolved", "withdrawn", "rejected",
)


def upgrade() -> None:
    op.create_table(
        "justice_complaints",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticket_number", sa.String(48), nullable=False, unique=True),
        sa.Column(
            "complaint_type",
            sa.Enum(*COMPLAINT_TYPES, name="justice_complaint_type"),
            nullable=False,
        ),
        sa.Column(
            "privacy_level",
            sa.Enum(*PRIVACY, name="justice_privacy_level"),
            nullable=False, server_default="confidential",
        ),
        sa.Column(
            "severity",
            sa.Enum(*SEVERITY, name="justice_severity"),
            nullable=False, server_default="medium",
        ),
        sa.Column(
            "status",
            sa.Enum(*STATUS, name="justice_status"),
            nullable=False, server_default="submitted",
        ),
        sa.Column("complainant_id_encrypted", sa.Text, nullable=True),
        sa.Column(
            "complainant_employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description_encrypted", sa.Text, nullable=False),
        sa.Column("desired_outcome_encrypted", sa.Text, nullable=True),
        sa.Column("incident_date", sa.Date, nullable=True),
        sa.Column("incident_location", sa.String(255), nullable=True),
        sa.Column("submitted_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("deadline_at", sa.DateTime, nullable=True),
        sa.Column(
            "assigned_to",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_complaints_ticket_number", "justice_complaints",
        ["ticket_number"], unique=True,
    )
    op.create_index(
        "ix_justice_complaints_status", "justice_complaints", ["status"]
    )

    op.create_table(
        "justice_evidence",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_url_encrypted", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_type", sa.String(64), nullable=True),
        sa.Column("file_hash", sa.String(96), nullable=True),
        sa.Column(
            "uploaded_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_evidence_complaint_id", "justice_evidence", ["complaint_id"]
    )

    op.create_table(
        "justice_accused",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("accused_name_encrypted", sa.Text, nullable=False),
        sa.Column(
            "accused_employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("relationship_type", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_accused_complaint_id", "justice_accused", ["complaint_id"]
    )

    op.create_table(
        "justice_witnesses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("witness_name_encrypted", sa.Text, nullable=False),
        sa.Column("witness_statement_encrypted", sa.Text, nullable=True),
        sa.Column("is_anonymous", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_witnesses_complaint_id", "justice_witnesses", ["complaint_id"]
    )

    op.create_table(
        "justice_actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "action_type",
            sa.Enum(
                "acknowledged", "assigned", "investigation_started", "comment",
                "warning_issued", "training_assigned", "transfer", "termination",
                "case_closed", "no_action",
                name="justice_action_type",
            ),
            nullable=False,
        ),
        sa.Column("action_date", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "taken_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes_encrypted", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_actions_complaint_id", "justice_actions", ["complaint_id"]
    )

    op.create_table(
        "justice_timeline",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(48), nullable=False),
        sa.Column("event_description", sa.Text, nullable=True),
        sa.Column("event_date", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "done_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_timeline_complaint_id", "justice_timeline", ["complaint_id"]
    )

    op.create_table(
        "justice_access_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(48), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_justice_access_log_complaint_id", "justice_access_log", ["complaint_id"]
    )

    op.create_table(
        "icc_members",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("member_name", sa.String(128), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "role",
            sa.Enum(
                "presiding_officer", "member", "external_member", "secretary",
                name="icc_role",
            ),
            nullable=False,
        ),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("is_external", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("term_start", sa.Date, nullable=False),
        sa.Column("term_end", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("contact", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "retaliation_flags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "complaint_id",
            sa.Integer,
            sa.ForeignKey("justice_complaints.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("flag_type", sa.String(48), nullable=False),
        sa.Column("detected_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "detected_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("resolved", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_retaliation_flags_complaint_id", "retaliation_flags", ["complaint_id"]
    )
    op.create_index(
        "ix_retaliation_flags_employee_id", "retaliation_flags", ["employee_id"]
    )

    op.create_table(
        "posh_annual_reports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("total_complaints", sa.Integer, server_default="0"),
        sa.Column("resolved", sa.Integer, server_default="0"),
        sa.Column("pending", sa.Integer, server_default="0"),
        sa.Column("actions_taken_json", sa.JSON, nullable=True),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "generated_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("year", name="uq_posh_annual_report_year"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )


def downgrade() -> None:
    op.drop_table("posh_annual_reports")
    op.drop_index("ix_retaliation_flags_employee_id", table_name="retaliation_flags")
    op.drop_index("ix_retaliation_flags_complaint_id", table_name="retaliation_flags")
    op.drop_table("retaliation_flags")
    op.drop_table("icc_members")
    op.drop_index("ix_justice_access_log_complaint_id", table_name="justice_access_log")
    op.drop_table("justice_access_log")
    op.drop_index("ix_justice_timeline_complaint_id", table_name="justice_timeline")
    op.drop_table("justice_timeline")
    op.drop_index("ix_justice_actions_complaint_id", table_name="justice_actions")
    op.drop_table("justice_actions")
    op.drop_index("ix_justice_witnesses_complaint_id", table_name="justice_witnesses")
    op.drop_table("justice_witnesses")
    op.drop_index("ix_justice_accused_complaint_id", table_name="justice_accused")
    op.drop_table("justice_accused")
    op.drop_index("ix_justice_evidence_complaint_id", table_name="justice_evidence")
    op.drop_table("justice_evidence")
    op.drop_index("ix_justice_complaints_status", table_name="justice_complaints")
    op.drop_index("ix_justice_complaints_ticket_number", table_name="justice_complaints")
    op.drop_table("justice_complaints")

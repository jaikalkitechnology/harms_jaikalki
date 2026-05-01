"""Polish features: assets, visitors, meeting rooms, internal job postings

Revision ID: 20260501_0016
Revises: 20260501_0015
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0016"
down_revision: Union[str, None] = "20260501_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    # ─── Assets ──────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_tag", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "laptop",
                "mobile",
                "headset",
                "monitor",
                "keyboard",
                "mouse",
                "vehicle",
                "other",
                name="asset_category",
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column("serial_number", sa.String(96), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column(
            "condition",
            sa.Enum(
                "new", "good", "fair", "damaged", "retired",
                name="asset_condition",
            ),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "in_stock", "assigned", "in_repair", "lost", "retired",
                name="asset_status",
            ),
            nullable=False,
            server_default="in_stock",
        ),
        sa.Column(
            "assigned_to",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("asset_tag", name="uq_asset_tag"),
        **_TABLE_KW,
    )
    op.create_index("ix_assets_assigned_to", "assets", ["assigned_to"])
    op.create_index("ix_assets_status", "assets", ["status"])

    op.create_table(
        "asset_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("returned_at", sa.DateTime(), nullable=True),
        sa.Column(
            "return_condition",
            sa.Enum(
                "good", "fair", "damaged", "lost",
                name="asset_return_condition",
            ),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_asset_assignments_asset_id", "asset_assignments", ["asset_id"]
    )
    op.create_index(
        "ix_asset_assignments_employee_id",
        "asset_assignments",
        ["employee_id"],
    )

    # ─── Visitors ────────────────────────────────────────────────────
    op.create_table(
        "visitors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("contact_email", sa.String(160), nullable=True),
        sa.Column("company", sa.String(160), nullable=True),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column(
            "host_employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expected_at", sa.DateTime(), nullable=False),
        sa.Column("qr_token", sa.String(96), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(), nullable=True),
        sa.Column("badge_number", sa.String(32), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "checked_in",
                "checked_out",
                "no_show",
                "cancelled",
                name="visitor_status",
            ),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("qr_token", name="uq_visitor_qr"),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_visitors_host_employee_id", "visitors", ["host_employee_id"]
    )
    op.create_index("ix_visitors_qr_token", "visitors", ["qr_token"])
    op.create_index("ix_visitors_status", "visitors", ["status"])

    # ─── Meeting rooms + bookings ────────────────────────────────────
    op.create_table(
        "meeting_rooms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("has_video", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "has_whiteboard", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_meeting_room_code"),
        **_TABLE_KW,
    )

    op.create_table(
        "meeting_room_bookings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("meeting_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "booked_by_employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("attendees", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "booked", "in_progress", "completed", "cancelled",
                name="room_booking_status",
            ),
            nullable=False,
            server_default="booked",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_meeting_room_bookings_room_id",
        "meeting_room_bookings",
        ["room_id"],
    )
    op.create_index(
        "ix_meeting_room_bookings_booked_by_employee_id",
        "meeting_room_bookings",
        ["booked_by_employee_id"],
    )
    op.create_index(
        "ix_meeting_room_bookings_start_time",
        "meeting_room_bookings",
        ["start_time"],
    )
    op.create_index(
        "ix_meeting_room_bookings_end_time",
        "meeting_room_bookings",
        ["end_time"],
    )
    op.create_index(
        "ix_meeting_room_bookings_status",
        "meeting_room_bookings",
        ["status"],
    )

    # ─── Internal job postings ───────────────────────────────────────
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("location", sa.String(120), nullable=True),
        sa.Column(
            "employment_type",
            sa.Enum(
                "full_time", "part_time", "contract", "intern",
                name="job_employment_type",
            ),
            nullable=False,
            server_default="full_time",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("referral_bonus", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "is_internal_only", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column(
            "posted_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("posted_at", sa.DateTime(), nullable=False),
        sa.Column("closes_on", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "published", "closed", "filled",
                name="job_posting_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code", name="uq_job_posting_code"),
        **_TABLE_KW,
    )
    op.create_index("ix_job_postings_status", "job_postings", ["status"])

    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "posting_id",
            sa.Integer(),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "applicant_employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("external_applicant_name", sa.String(160), nullable=True),
        sa.Column("external_applicant_email", sa.String(160), nullable=True),
        sa.Column(
            "referrer_employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("cover_note", sa.Text(), nullable=True),
        sa.Column("resume_url", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "submitted",
                "shortlisted",
                "interviewing",
                "offered",
                "hired",
                "rejected",
                "withdrawn",
                name="job_application_status",
            ),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column(
            "referral_bonus_paid",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "posting_id",
            "applicant_employee_id",
            name="uq_application_posting_applicant",
        ),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_job_applications_posting_id", "job_applications", ["posting_id"]
    )
    op.create_index(
        "ix_job_applications_applicant_employee_id",
        "job_applications",
        ["applicant_employee_id"],
    )
    op.create_index(
        "ix_job_applications_referrer_employee_id",
        "job_applications",
        ["referrer_employee_id"],
    )
    op.create_index(
        "ix_job_applications_status", "job_applications", ["status"]
    )


def downgrade() -> None:
    op.drop_table("job_applications")
    op.drop_table("job_postings")
    op.drop_table("meeting_room_bookings")
    op.drop_table("meeting_rooms")
    op.drop_table("visitors")
    op.drop_table("asset_assignments")
    op.drop_table("assets")

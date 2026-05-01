"""Field Force Core: customers, jobs, visits, photos, location tracks

Revision ID: 20260501_0008
Revises: 20260501_0007
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0008"
down_revision: Union[str, None] = "20260501_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "field_employees",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum("sales", "service", "delivery", "trainer", "other",
                    name="field_type"),
            nullable=False, server_default="sales",
        ),
        sa.Column("territory", sa.String(96), nullable=True),
        sa.Column(
            "vehicle_type",
            sa.Enum("two_wheeler", "four_wheeler", "public_transport", "walk",
                    name="vehicle_type"),
            nullable=True,
        ),
        sa.Column("vehicle_number", sa.String(32), nullable=True),
        sa.Column("license_number", sa.String(48), nullable=True),
        sa.Column(
            "current_status",
            sa.Enum("idle", "on_visit", "in_transit", "off_duty",
                    name="field_employee_status"),
            nullable=False, server_default="idle",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("employee_id", name="uq_field_employee_employee_id"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column(
            "type",
            sa.Enum("lead", "prospect", "customer", "partner",
                    name="customer_type"),
            nullable=False, server_default="lead",
        ),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.String(96), nullable=True),
        sa.Column("state", sa.String(96), nullable=True),
        sa.Column("pincode", sa.String(16), nullable=True),
        sa.Column("geo_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("geo_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("industry", sa.String(96), nullable=True),
        sa.Column("gst", sa.String(32), nullable=True),
        sa.Column("pan", sa.String(16), nullable=True),
        sa.Column("contact_persons", sa.JSON, nullable=True),
        sa.Column("territory", sa.String(96), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_customers_name", "customers", ["name"])

    op.create_table(
        "field_jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "job_type",
            sa.Enum(
                "sales_call", "demo", "service", "delivery", "training",
                "collection", "survey", "other",
                name="field_job_type",
            ),
            nullable=False, server_default="sales_call",
        ),
        sa.Column("scheduled_date", sa.Date, nullable=False),
        sa.Column("scheduled_time", sa.String(8), nullable=True),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "urgent", name="field_job_priority"),
            nullable=False, server_default="medium",
        ),
        sa.Column(
            "status",
            sa.Enum("scheduled", "in_progress", "completed", "cancelled", "skipped",
                    name="field_job_status"),
            nullable=False, server_default="scheduled",
        ),
        sa.Column("notes", sa.Text),
        sa.Column(
            "assigned_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_field_jobs_employee_id", "field_jobs", ["employee_id"])
    op.create_index("ix_field_jobs_scheduled_date", "field_jobs", ["scheduled_date"])
    op.create_index("ix_field_jobs_status", "field_jobs", ["status"])

    op.create_table(
        "field_visits",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            sa.Integer,
            sa.ForeignKey("field_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_in_time", sa.DateTime, nullable=True),
        sa.Column("check_in_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("check_in_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("check_in_distance_m", sa.Integer, nullable=True),
        sa.Column("check_in_selfie_url", sa.String(500), nullable=True),
        sa.Column("check_in_is_mock", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("check_out_time", sa.DateTime, nullable=True),
        sa.Column("check_out_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("check_out_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("visit_form", sa.JSON, nullable=True),
        sa.Column("outcome", sa.String(96), nullable=True),
        sa.Column("notes", sa.Text),
        sa.Column("signature_url", sa.String(500), nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("job_id", name="uq_visit_job"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_field_visits_employee_id", "field_visits", ["employee_id"])

    op.create_table(
        "field_visit_photos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "visit_id",
            sa.Integer,
            sa.ForeignKey("field_visits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("photo_url", sa.String(500), nullable=False),
        sa.Column(
            "photo_type",
            sa.Enum(
                "storefront", "shelf", "product", "document", "selfie", "other",
                name="visit_photo_type",
            ),
            nullable=False, server_default="other",
        ),
        sa.Column("geo_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("geo_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("taken_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("watermarked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_field_visit_photos_visit_id", "field_visit_photos", ["visit_id"])

    op.create_table(
        "field_location_tracks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lat", sa.Numeric(10, 7), nullable=False),
        sa.Column("lng", sa.Numeric(10, 7), nullable=False),
        sa.Column("accuracy_m", sa.Integer, nullable=True),
        sa.Column("speed_mps", sa.Numeric(6, 2), nullable=True),
        sa.Column("heading", sa.Numeric(6, 2), nullable=True),
        sa.Column("battery_pct", sa.Integer, nullable=True),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_field_location_tracks_employee_id", "field_location_tracks", ["employee_id"])
    op.create_index("ix_field_location_tracks_timestamp", "field_location_tracks", ["timestamp"])

    op.create_table(
        "field_expenses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "visit_id",
            sa.Integer,
            sa.ForeignKey("field_visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "fuel", "toll", "parking", "food", "lodging", "phone", "other",
                name="field_expense_category",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", "reimbursed",
                    name="field_expense_status"),
            nullable=False, server_default="pending",
        ),
        sa.Column(
            "approver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_field_expenses_employee_id", "field_expenses", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_field_expenses_employee_id", table_name="field_expenses")
    op.drop_table("field_expenses")
    op.drop_index("ix_field_location_tracks_timestamp", table_name="field_location_tracks")
    op.drop_index("ix_field_location_tracks_employee_id", table_name="field_location_tracks")
    op.drop_table("field_location_tracks")
    op.drop_index("ix_field_visit_photos_visit_id", table_name="field_visit_photos")
    op.drop_table("field_visit_photos")
    op.drop_index("ix_field_visits_employee_id", table_name="field_visits")
    op.drop_table("field_visits")
    op.drop_index("ix_field_jobs_status", table_name="field_jobs")
    op.drop_index("ix_field_jobs_scheduled_date", table_name="field_jobs")
    op.drop_index("ix_field_jobs_employee_id", table_name="field_jobs")
    op.drop_table("field_jobs")
    op.drop_index("ix_customers_name", table_name="customers")
    op.drop_table("customers")
    op.drop_table("field_employees")

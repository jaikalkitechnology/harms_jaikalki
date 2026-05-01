"""Employee master, salary templates, probation, intern expenses

Revision ID: 20260501_0002
Revises: 20260501_0001
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0002"
down_revision: Union[str, None] = "20260501_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "employee_categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("eligible_for_pf", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("eligible_for_esic", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("eligible_for_gratuity", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("eligible_for_pl", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("eligible_for_bonus", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("has_salary", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("has_stipend", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("only_travel_expense", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("requires_probation", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("default_probation_months", sa.Integer, nullable=False, server_default="6"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "salary_templates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("template_code", sa.String(48), nullable=False, unique=True),
        sa.Column("template_name", sa.String(96), nullable=False),
        sa.Column(
            "category",
            sa.Enum("intern", "trainee", "permanent", "contract",
                    name="salary_template_category"),
            nullable=False,
        ),
        sa.Column("designation_level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("ctc_annual_default", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("basic_amount", sa.Numeric(10, 2), server_default="0"),
        sa.Column("basic_percentage", sa.Numeric(5, 2), server_default="50"),
        sa.Column("hra_amount", sa.Numeric(10, 2), server_default="0"),
        sa.Column("hra_percentage", sa.Numeric(5, 2), server_default="30"),
        sa.Column("other_allowance", sa.Numeric(10, 2), server_default="0"),
        sa.Column("special_allowance", sa.Numeric(10, 2), server_default="0"),
        sa.Column("conveyance", sa.Numeric(10, 2), server_default="0"),
        sa.Column("medical_allowance", sa.Numeric(10, 2), server_default="0"),
        sa.Column("lta", sa.Numeric(10, 2), server_default="0"),
        sa.Column("food_coupon", sa.Numeric(10, 2), server_default="0"),
        sa.Column("travel_expense_max", sa.Numeric(10, 2), server_default="0"),
        sa.Column("is_paid_internship", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("has_probation", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("probation_months", sa.Integer, nullable=False, server_default="6"),
        sa.Column("probation_extension_months", sa.Integer, nullable=False, server_default="2"),
        sa.Column("mediclaim_amount", sa.Numeric(12, 2), server_default="200000"),
        sa.Column("pa_insurance_amount", sa.Numeric(12, 2), server_default="500000"),
        sa.Column("notice_period_probation", sa.Integer, server_default="15"),
        sa.Column("notice_period_confirmed", sa.Integer, server_default="30"),
        sa.Column("notice_period_termination", sa.Integer, server_default="7"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            unique=True,
            nullable=True,
        ),
        sa.Column("employee_code", sa.String(20), nullable=False, unique=True),
        sa.Column("first_name", sa.String(64), nullable=False),
        sa.Column("last_name", sa.String(64), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("blood_group", sa.String(8), nullable=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("marital_status", sa.String(16), nullable=True),
        sa.Column("personal_email", sa.String(191), nullable=True),
        sa.Column("personal_phone", sa.String(32), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("employee_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "designation_id",
            sa.Integer,
            sa.ForeignKey("designations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            sa.Integer,
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reporting_to",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("date_of_joining", sa.Date, nullable=True),
        sa.Column("probation_end_date", sa.Date, nullable=True),
        sa.Column("confirmation_date", sa.Date, nullable=True),
        sa.Column("exit_date", sa.Date, nullable=True),
        sa.Column(
            "salary_template_id",
            sa.Integer,
            sa.ForeignKey("salary_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ctc_annual", sa.Numeric(12, 2), server_default="0"),
        sa.Column(
            "work_location", sa.String(200), nullable=False,
            server_default="Mira Road, Thane",
        ),
        sa.Column("employment_type", sa.String(32), nullable=False, server_default="full_time"),
        sa.Column("work_mode", sa.String(16), nullable=False, server_default="office"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_on_probation", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"], unique=True)

    op.create_table(
        "employee_probation",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("probation_start_date", sa.Date, nullable=False),
        sa.Column("probation_end_date", sa.Date, nullable=False),
        sa.Column("is_extended", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("extension_end_date", sa.Date, nullable=True),
        sa.Column("extension_reason", sa.Text),
        sa.Column(
            "status",
            sa.Enum(
                "in_progress", "extended", "confirmed", "terminated",
                name="probation_status",
            ),
            nullable=False, server_default="in_progress",
        ),
        sa.Column("confirmed_date", sa.Date, nullable=True),
        sa.Column("confirmation_letter_url", sa.String(500), nullable=True),
        sa.Column(
            "confirmed_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_employee_probation_employee_id", "employee_probation", ["employee_id"])

    op.create_table(
        "employee_documents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("doc_type", sa.String(48), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer, server_default="0"),
        sa.Column("mime_type", sa.String(96), nullable=True),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.Date, nullable=True),
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
    op.create_index("ix_employee_documents_employee_id", "employee_documents", ["employee_id"])

    op.create_table(
        "employee_addresses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(16), nullable=False, server_default="current"),
        sa.Column("line1", sa.String(255), nullable=False),
        sa.Column("line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(96), nullable=False),
        sa.Column("state", sa.String(96), nullable=False),
        sa.Column("pincode", sa.String(16), nullable=False),
        sa.Column("country", sa.String(64), nullable=False, server_default="India"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_employee_addresses_employee_id", "employee_addresses", ["employee_id"])

    op.create_table(
        "employee_bank_details",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("account_no", sa.String(32), nullable=False),
        sa.Column("ifsc", sa.String(16), nullable=False),
        sa.Column("bank_name", sa.String(96), nullable=False),
        sa.Column("branch", sa.String(96), nullable=True),
        sa.Column("account_holder_name", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "emergency_contacts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column("relation", sa.String(32), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_emergency_contacts_employee_id", "emergency_contacts", ["employee_id"])

    op.create_table(
        "family_members",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column("relation", sa.String(32), nullable=False),
        sa.Column("dob", sa.Date, nullable=True),
        sa.Column("is_dependent", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_family_members_employee_id", "family_members", ["employee_id"])

    op.create_table(
        "intern_travel_expenses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column(
            "expense_type",
            sa.Enum(
                "local_travel", "office_commute", "project_visit",
                name="intern_expense_type",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", "reimbursed",
                name="intern_expense_status",
            ),
            nullable=False, server_default="pending",
        ),
        sa.Column(
            "approved_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("reimbursed_at", sa.DateTime, nullable=True),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_intern_travel_expenses_employee_id",
        "intern_travel_expenses",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_intern_travel_expenses_employee_id", table_name="intern_travel_expenses")
    op.drop_table("intern_travel_expenses")
    op.drop_index("ix_family_members_employee_id", table_name="family_members")
    op.drop_table("family_members")
    op.drop_index("ix_emergency_contacts_employee_id", table_name="emergency_contacts")
    op.drop_table("emergency_contacts")
    op.drop_table("employee_bank_details")
    op.drop_index("ix_employee_addresses_employee_id", table_name="employee_addresses")
    op.drop_table("employee_addresses")
    op.drop_index("ix_employee_documents_employee_id", table_name="employee_documents")
    op.drop_table("employee_documents")
    op.drop_index("ix_employee_probation_employee_id", table_name="employee_probation")
    op.drop_table("employee_probation")
    op.drop_index("ix_employees_employee_code", table_name="employees")
    op.drop_table("employees")
    op.drop_table("salary_templates")
    op.drop_table("employee_categories")

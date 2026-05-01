"""Payroll: runs, payslips, reimbursements, declarations, generated docs

Revision ID: 20260501_0006
Revises: 20260501_0005
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0006"
down_revision: Union[str, None] = "20260501_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "payroll_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "processed", "finalized", "reverted",
                name="payroll_run_status",
            ),
            nullable=False, server_default="draft",
        ),
        sa.Column(
            "run_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("run_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("finalized_at", sa.DateTime, nullable=True),
        sa.Column(
            "finalized_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("total_gross", sa.Numeric(14, 2), server_default="0"),
        sa.Column("total_net", sa.Numeric(14, 2), server_default="0"),
        sa.Column("total_employer_cost", sa.Numeric(14, 2), server_default="0"),
        sa.Column("total_employees", sa.Integer, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text),
        sa.UniqueConstraint("year", "month", name="uq_payroll_run_period"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "payslips",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "payroll_run_id",
            sa.Integer,
            sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("breakup", sa.JSON, nullable=False),
        sa.Column("basic", sa.Numeric(12, 2), server_default="0"),
        sa.Column("hra", sa.Numeric(12, 2), server_default="0"),
        sa.Column("other_allowance", sa.Numeric(12, 2), server_default="0"),
        sa.Column("gross", sa.Numeric(12, 2), server_default="0"),
        sa.Column("pf_employee", sa.Numeric(12, 2), server_default="0"),
        sa.Column("esic_employee", sa.Numeric(12, 2), server_default="0"),
        sa.Column("professional_tax", sa.Numeric(12, 2), server_default="0"),
        sa.Column("tds", sa.Numeric(12, 2), server_default="0"),
        sa.Column("other_deductions", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_deductions", sa.Numeric(12, 2), server_default="0"),
        sa.Column("net_pay", sa.Numeric(12, 2), server_default="0"),
        sa.Column("pf_employer", sa.Numeric(12, 2), server_default="0"),
        sa.Column("esic_employer", sa.Numeric(12, 2), server_default="0"),
        sa.Column("days_paid", sa.Numeric(5, 2), server_default="0"),
        sa.Column("days_lop", sa.Numeric(5, 2), server_default="0"),
        sa.Column("working_days", sa.Numeric(5, 2), server_default="0"),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.UniqueConstraint(
            "payroll_run_id", "employee_id", name="uq_payslip_run_employee"
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_payslips_employee_id", "payslips", ["employee_id"])

    op.create_table(
        "reimbursements",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "travel", "food", "internet", "phone", "medical", "books", "other",
                name="reimbursement_category",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("bill_url", sa.String(500), nullable=True),
        sa.Column("bill_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", "paid",
                name="reimbursement_status",
            ),
            nullable=False, server_default="pending",
        ),
        sa.Column(
            "approver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column(
            "paid_in_run_id",
            sa.Integer,
            sa.ForeignKey("payroll_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_reimbursements_employee_id", "reimbursements", ["employee_id"]
    )

    op.create_table(
        "investment_declarations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fy", sa.String(8), nullable=False),
        sa.Column(
            "regime",
            sa.Enum("old", "new", name="tax_regime"),
            nullable=False, server_default="new",
        ),
        sa.Column("locked_at", sa.DateTime, nullable=True),
        sa.Column("section_80c", sa.Numeric(12, 2), server_default="0"),
        sa.Column("section_80d", sa.Numeric(12, 2), server_default="0"),
        sa.Column("hra_exemption", sa.Numeric(12, 2), server_default="0"),
        sa.Column("home_loan_interest", sa.Numeric(12, 2), server_default="0"),
        sa.Column("educational_loan", sa.Numeric(12, 2), server_default="0"),
        sa.Column("donations_80g", sa.Numeric(12, 2), server_default="0"),
        sa.Column("other", sa.JSON, nullable=True),
        sa.UniqueConstraint("employee_id", "fy", name="uq_investment_decl_emp_fy"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_investment_declarations_employee_id",
        "investment_declarations",
        ["employee_id"],
    )

    op.create_table(
        "bank_file_exports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "payroll_run_id",
            sa.Integer,
            sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("bank_format", sa.String(32), nullable=False, server_default="csv"),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_employees", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_bank_file_exports_payroll_run_id",
        "bank_file_exports",
        ["payroll_run_id"],
    )

    op.create_table(
        "generated_documents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "doc_type",
            sa.Enum(
                "offer_letter", "confirmation_letter", "payslip", "form16",
                "intern_reimbursement",
                name="generated_doc_type",
            ),
            nullable=False,
        ),
        sa.Column("letter_number", sa.String(48), nullable=True),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column(
            "generated_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_generated_documents_employee_id",
        "generated_documents",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_generated_documents_employee_id", table_name="generated_documents"
    )
    op.drop_table("generated_documents")
    op.drop_index(
        "ix_bank_file_exports_payroll_run_id", table_name="bank_file_exports"
    )
    op.drop_table("bank_file_exports")
    op.drop_index(
        "ix_investment_declarations_employee_id",
        table_name="investment_declarations",
    )
    op.drop_table("investment_declarations")
    op.drop_index("ix_reimbursements_employee_id", table_name="reimbursements")
    op.drop_table("reimbursements")
    op.drop_index("ix_payslips_employee_id", table_name="payslips")
    op.drop_table("payslips")
    op.drop_table("payroll_runs")

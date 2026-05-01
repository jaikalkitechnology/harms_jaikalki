"""Attendance, shifts, leave, holidays, comp-off

Revision ID: 20260501_0003
Revises: 20260501_0002
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0003"
down_revision: Union[str, None] = "20260501_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("break_duration_min", sa.Integer, nullable=False, server_default="60"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "employee_shifts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "shift_id",
            sa.Integer,
            sa.ForeignKey("shifts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_employee_shifts_employee_id", "employee_shifts", ["employee_id"])

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("check_in", sa.DateTime, nullable=True),
        sa.Column("check_in_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("check_in_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("check_in_selfie_url", sa.String(500), nullable=True),
        sa.Column("check_in_distance_m", sa.Integer, nullable=True),
        sa.Column("check_out", sa.DateTime, nullable=True),
        sa.Column("check_out_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("check_out_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "present", "absent", "half_day", "wfh", "leave", "holiday",
                name="attendance_status",
            ),
            nullable=False,
            server_default="absent",
        ),
        sa.Column(
            "work_mode",
            sa.Enum("office", "wfh", "hybrid", "field", name="attendance_work_mode"),
            nullable=False,
            server_default="office",
        ),
        sa.Column(
            "source",
            sa.Enum("gps", "manual", "admin", "import", name="attendance_source"),
            nullable=False,
            server_default="gps",
        ),
        sa.Column("total_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text),
        sa.UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_attendance_employee_id", "attendance", ["employee_id"])
    op.create_index("ix_attendance_date", "attendance", ["date"])

    op.create_table(
        "attendance_regularizations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("requested_check_in", sa.DateTime, nullable=True),
        sa.Column("requested_check_out", sa.DateTime, nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="regularization_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "approver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("decision_comment", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_attendance_regularizations_employee_id",
        "attendance_regularizations",
        ["employee_id"],
    )

    op.create_table(
        "leave_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("days_per_year", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("carry_forward", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("max_carry_forward", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("encashable", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "requires_attachment_after_days",
            sa.Integer, nullable=False, server_default="0",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )

    op.create_table(
        "leave_balances",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "leave_type_id",
            sa.Integer,
            sa.ForeignKey("leave_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("allocated", sa.Numeric(5, 2), server_default="0"),
        sa.Column("used", sa.Numeric(5, 2), server_default="0"),
        sa.Column("carried_forward", sa.Numeric(5, 2), server_default="0"),
        sa.UniqueConstraint(
            "employee_id", "leave_type_id", "year", name="uq_balance_emp_type_year"
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_leave_balances_employee_id", "leave_balances", ["employee_id"])

    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "leave_type_id",
            sa.Integer,
            sa.ForeignKey("leave_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("from_date", sa.Date, nullable=False),
        sa.Column("to_date", sa.Date, nullable=False),
        sa.Column("days", sa.Numeric(5, 2), nullable=False),
        sa.Column("half_day", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("reason", sa.Text),
        sa.Column("attachment_url", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", "cancelled",
                name="leave_request_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("applied_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "approver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("decision_comment", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_leave_requests_employee_id", "leave_requests", ["employee_id"])

    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column(
            "type",
            sa.Enum("national", "regional", "company", name="holiday_type"),
            nullable=False, server_default="national",
        ),
        sa.Column("is_optional", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("location", sa.String(64), nullable=False, server_default="ALL"),
        sa.UniqueConstraint("date", "location", name="uq_holiday_date_location"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_holidays_date", "holidays", ["date"])

    op.create_table(
        "comp_off",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer,
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("earned_date", sa.Date, nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=False),
        sa.Column("days", sa.Numeric(5, 2), server_default="1"),
        sa.Column(
            "status",
            sa.Enum("active", "used", "expired", "rejected", name="comp_off_status"),
            nullable=False, server_default="active",
        ),
        sa.Column(
            "used_for_request_id",
            sa.Integer,
            sa.ForeignKey("leave_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        **_TABLE_KW,
    )
    op.create_index("ix_comp_off_employee_id", "comp_off", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_comp_off_employee_id", table_name="comp_off")
    op.drop_table("comp_off")
    op.drop_index("ix_holidays_date", table_name="holidays")
    op.drop_table("holidays")
    op.drop_index("ix_leave_requests_employee_id", table_name="leave_requests")
    op.drop_table("leave_requests")
    op.drop_index("ix_leave_balances_employee_id", table_name="leave_balances")
    op.drop_table("leave_balances")
    op.drop_table("leave_types")
    op.drop_index(
        "ix_attendance_regularizations_employee_id",
        table_name="attendance_regularizations",
    )
    op.drop_table("attendance_regularizations")
    op.drop_index("ix_attendance_date", table_name="attendance")
    op.drop_index("ix_attendance_employee_id", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index("ix_employee_shifts_employee_id", table_name="employee_shifts")
    op.drop_table("employee_shifts")
    op.drop_table("shifts")

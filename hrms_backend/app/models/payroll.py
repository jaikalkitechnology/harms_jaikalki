from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class PayrollRun(Base, TimestampMixin):
    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_payroll_run_period"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    status: Mapped[str] = mapped_column(
        Enum("draft", "processed", "finalized", "reverted", name="payroll_run_status"),
        default="draft",
        nullable=False,
    )
    run_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finalized_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    total_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_net: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_employer_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0")
    )
    total_employees: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Attendance cycle this run was computed against (1 = calendar
    # month, 21 = 21st-prev → 20th-current, etc.).
    cycle_start_day: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    # Salary distributed / paid-out marker. Set once the bank transfer
    # is done — independent of the processed→finalized status flow.
    disbursed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    disbursed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    disbursed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    payslips: Mapped[List["Payslip"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", lazy="selectin"
    )


class Payslip(Base, TimestampMixin):
    __tablename__ = "payslips"
    __table_args__ = (
        UniqueConstraint(
            "payroll_run_id", "employee_id", name="uq_payslip_run_employee"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payroll_run_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot of the breakup (matches JaikalkiSalaryCalculator output).
    breakup: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    basic: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    hra: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    other_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    pf_employee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    esic_employee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    professional_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    tds: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    other_deductions: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    total_deductions: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )

    net_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    pf_employer: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    esic_employer: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    days_paid: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    days_lop: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    working_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    # Day-class breakdown so admins can see *why* the LOP came out the
    # way it did. Always recomputable from attendance + leaves.
    days_present: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    days_paid_leave: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    days_unpaid_leave: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    days_absent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    days_holiday: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    days_weekoff: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    days_sandwich: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0")
    )
    # Final salary of a resigned / terminated employee whose last
    # working day falls inside this run's attendance window.
    is_final_settlement: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # Held back from the bank file and the employee's app until the
    # resignation is marked settled.
    on_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # PF / EPS wages actually used this month (earned basic capped at the
    # wage-month ceiling). The ECR challan reads these so an old month's
    # challan stays correct after the cap changes.
    pf_wages: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    eps_wages: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    edli_wages: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # Approved incentives paid with this slip (part of gross).
    incentive: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    run: Mapped["PayrollRun"] = relationship(back_populates="payslips")


class Reimbursement(Base, TimestampMixin):
    __tablename__ = "reimbursements"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        Enum(
            "travel",
            "food",
            "internet",
            "phone",
            "medical",
            "books",
            "other",
            name="reimbursement_category",
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bill_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "approved",
            "rejected",
            "paid",
            name="reimbursement_status",
        ),
        default="pending",
        nullable=False,
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_in_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InvestmentDeclaration(Base, TimestampMixin):
    __tablename__ = "investment_declarations"
    __table_args__ = (
        UniqueConstraint("employee_id", "fy", name="uq_investment_decl_emp_fy"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fy: Mapped[str] = mapped_column(String(8), nullable=False)  # e.g. "2025-26"
    regime: Mapped[str] = mapped_column(
        Enum("old", "new", name="tax_regime"), default="new", nullable=False
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    section_80c: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    section_80d: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    hra_exemption: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    home_loan_interest: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    educational_loan: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    donations_80g: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    other: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class BankFileExport(Base, TimestampMixin):
    __tablename__ = "bank_file_exports"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payroll_run_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    bank_format: Mapped[str] = mapped_column(String(32), default="csv", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    total_employees: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class GeneratedDocument(Base, TimestampMixin):
    """Generated PDFs (offer letter, confirmation letter, payslip) so we can
    audit re-issuance and store the assigned letter number."""

    __tablename__ = "generated_documents"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(
        Enum(
            "offer_letter",
            "confirmation_letter",
            "payslip",
            "form16",
            "intern_reimbursement",
            name="generated_doc_type",
        ),
        nullable=False,
    )
    letter_number: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class PfWageCeiling(Base, TimestampMixin):
    """Dated PF wage ceiling register (EPFO wage cap).

    The cap for a payroll month is the day-weighted cap across that wage
    month (see pf_ceiling_service.caps_for_wage_month). Records are never
    overwritten so historical payrolls stay reproducible.
    """

    __tablename__ = "pf_wage_ceilings"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cap_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # EPS (pension) has its own wage ceiling; defaults to the PF cap
    # only if the circular raises both.
    eps_cap_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # EDLI (insurance) wage ceiling — ₹15,000 unless the circular changes it.
    edli_cap_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("15000")
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    # How a mid-month effective date treats that wage month:
    #   day_weighted — pro-rata by calendar days (default)
    #   whole_month  — the whole effective month uses the new cap
    #   next_month   — the new cap starts from the next wage month
    mid_month_mode: Mapped[str] = mapped_column(
        Enum("day_weighted", "whole_month", "next_month", name="pf_ceiling_mode"),
        default="day_weighted",
        nullable=False,
    )
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

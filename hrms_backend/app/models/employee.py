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
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class EmployeeCategory(Base, TimestampMixin):
    __tablename__ = "employee_categories"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    eligible_for_pf: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    eligible_for_esic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    eligible_for_gratuity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    eligible_for_pl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    eligible_for_bonus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    has_salary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_stipend: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    only_travel_expense: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    requires_probation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_probation_months: Mapped[int] = mapped_column(Integer, default=6, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SalaryTemplate(Base, TimestampMixin):
    __tablename__ = "salary_templates"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    template_name: Mapped[str] = mapped_column(String(96), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum("intern", "trainee", "permanent", "contract", name="salary_template_category"),
        nullable=False,
    )
    designation_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Defaults — calculator can override using ratios + ctc_annual.
    ctc_annual_default: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )

    basic_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    basic_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50"))
    hra_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    hra_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("30"))
    other_allowance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    special_allowance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    conveyance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    medical_allowance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    lta: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    food_coupon: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))

    travel_expense_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    is_paid_internship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    has_probation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    probation_months: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    probation_extension_months: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    mediclaim_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("200000")
    )
    pa_insurance_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("500000")
    )

    notice_period_probation: Mapped[int] = mapped_column(Integer, default=15)
    notice_period_confirmed: Mapped[int] = mapped_column(Integer, default=30)
    notice_period_termination: Mapped[int] = mapped_column(Integer, default=7)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    employee_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    blood_group: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    personal_email: Mapped[Optional[str]] = mapped_column(String(191), nullable=True)
    personal_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee_categories.id", ondelete="SET NULL"), nullable=True
    )
    designation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("designations.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    reporting_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    date_of_joining: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    probation_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confirmation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Self-service resignation gate: admin must flip this to True before
    # the employee can submit a resignation from the mobile app. Auto-
    # locks again after a successful submission so they can't double-file.
    resignation_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    salary_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("salary_templates.id", ondelete="SET NULL"), nullable=True
    )
    ctc_annual: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # Per-employee statutory overrides. Templates carry the salary
    # *structure*; these flags carry the statutory deviations that vary
    # employee-by-employee (PF opt-out for >₹15k basic, custom PF cap,
    # ESIC exemption for international/contractor cases, and the PT
    # state which drives the Professional Tax slab).
    pf_opt_out: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    pf_basic_cap_override: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    esic_force_exempt: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    pt_state: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Statutory IDs (issued externally; we just record them).
    pf_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    uan_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    esic_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Group health / accident insurance (Mediclaim, GPA, etc.)
    insurance_company: Mapped[Optional[str]] = mapped_column(
        String(160), nullable=True
    )
    insurance_policy_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # Per-employee attendance / payroll cycle. 1 = calendar month
    # (1→last day). 21 = 21st of prev month → 20th of current month, etc.
    # Calendar + payroll services read this when slicing the period.
    attendance_cycle_start_day: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    # Admin-granted window during which the employee may self-mark
    # back-dated attendance from the mobile app. Both null ⇒ only the
    # current day can be self-marked.
    backdate_from: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    backdate_to: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )

    work_location: Mapped[str] = mapped_column(
        String(200), default="Mira Road, Thane", nullable=False
    )
    employment_type: Mapped[str] = mapped_column(String(32), default="full_time", nullable=False)
    work_mode: Mapped[str] = mapped_column(String(16), default="office", nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_on_probation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Optional["EmployeeCategory"]] = relationship(
        "EmployeeCategory", lazy="joined"
    )
    designation: Mapped[Optional["Designation"]] = relationship(  # noqa: F821
        "Designation", lazy="joined"
    )
    department: Mapped[Optional["Department"]] = relationship(  # noqa: F821
        "Department", lazy="joined"
    )
    salary_template: Mapped[Optional["SalaryTemplate"]] = relationship(
        "SalaryTemplate", lazy="joined"
    )
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", remote_side="Employee.id", lazy="joined"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class EmployeeProbation(Base, TimestampMixin):
    __tablename__ = "employee_probation"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    probation_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    probation_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_extended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extension_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    extension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "in_progress",
            "extended",
            "confirmed",
            "terminated",
            name="probation_status",
        ),
        default="in_progress",
        nullable=False,
    )
    confirmed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confirmation_letter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confirmed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class EmployeeDocument(Base, TimestampMixin):
    __tablename__ = "employee_documents"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(48), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class EmployeeAddress(Base, TimestampMixin):
    __tablename__ = "employee_addresses"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(16), default="current", nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(96), nullable=False)
    state: Mapped[str] = mapped_column(String(96), nullable=False)
    pincode: Mapped[str] = mapped_column(String(16), nullable=False)
    country: Mapped[str] = mapped_column(String(64), default="India", nullable=False)


class EmployeeBankDetails(Base, TimestampMixin):
    __tablename__ = "employee_bank_details"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    account_no: Mapped[str] = mapped_column(String(32), nullable=False)
    ifsc: Mapped[str] = mapped_column(String(16), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(96), nullable=False)
    branch: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    account_holder_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class EmergencyContact(Base, TimestampMixin):
    __tablename__ = "emergency_contacts"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    relation: Mapped[str] = mapped_column(String(32), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class FamilyMember(Base, TimestampMixin):
    __tablename__ = "family_members"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    relation: Mapped[str] = mapped_column(String(32), nullable=False)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_dependent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class InternTravelExpense(Base, TimestampMixin):
    __tablename__ = "intern_travel_expenses"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    expense_type: Mapped[str] = mapped_column(
        Enum(
            "local_travel",
            "office_commute",
            "project_visit",
            name="intern_expense_type",
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "approved",
            "rejected",
            "reimbursed",
            name="intern_expense_status",
        ),
        default="pending",
        nullable=False,
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reimbursed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class EmployeePassport(Base, TimestampMixin):
    """Passport + visa held against the employee.

    One row per employee — the same passport often carries multiple
    visas, but the active one is captured here. Older visas live in
    `employee_documents` as scanned uploads.
    """

    __tablename__ = "employee_passports"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    passport_no: Mapped[str] = mapped_column(String(32), nullable=False)
    passport_country: Mapped[str] = mapped_column(
        String(64), default="India", nullable=False
    )
    passport_issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    passport_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    passport_place_of_issue: Mapped[Optional[str]] = mapped_column(
        String(96), nullable=True
    )
    visa_no: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    visa_type: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    visa_country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    visa_issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    visa_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class EmployeeNominee(Base, TimestampMixin):
    """PF / Gratuity / Insurance nominee. Up to 4 per employee — share %
    must total 100 across them when set."""

    __tablename__ = "employee_nominees"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    relation: Mapped[str] = mapped_column(String(32), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    share_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100"), nullable=False
    )
    nominee_type: Mapped[str] = mapped_column(
        Enum(
            "pf",
            "gratuity",
            "insurance",
            "general",
            name="nominee_type",
        ),
        default="general",
        nullable=False,
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    id_proof_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_minor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)


class AttendanceCycle(Base, TimestampMixin):
    """Catalog of attendance / payroll cycles the company runs.

    Employees pick one via `Employee.attendance_cycle_start_day`. The
    table is here so HR can add new cycles (e.g. 11→10) without
    code changes; the integer column on Employee stays the source of
    truth at runtime.
    """

    __tablename__ = "attendance_cycles"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    start_day: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

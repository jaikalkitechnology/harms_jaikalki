from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Lookups ─────────────────────────────────────────────────────────────
class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: Optional[str] = None
    eligible_for_pf: bool
    eligible_for_esic: bool
    eligible_for_gratuity: bool
    has_salary: bool
    only_travel_expense: bool
    requires_probation: bool
    default_probation_months: int


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: Optional[str] = None
    head_id: Optional[int] = None


class DesignationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    level: int
    department_id: Optional[int] = None


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=96)
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=96)
    description: Optional[str] = None
    head_id: Optional[int] = None


class DesignationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=96)
    level: int = Field(default=1, ge=1, le=10)
    department_id: Optional[int] = None


class DesignationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=96)
    level: Optional[int] = Field(default=None, ge=1, le=10)
    department_id: Optional[int] = None


# ── Shifts ──────────────────────────────────────────────────────────────
from datetime import time as _time  # noqa: E402


class ShiftCreate(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=64)
    start_time: _time
    end_time: _time
    break_duration_min: int = Field(default=60, ge=0, le=480)
    is_default: bool = False
    is_active: bool = True


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[_time] = None
    end_time: Optional[_time] = None
    break_duration_min: Optional[int] = Field(default=None, ge=0, le=480)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


# ── Salary templates ────────────────────────────────────────────────────
class SalaryTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    template_code: str
    template_name: str
    category: str
    designation_level: int
    ctc_annual_default: Decimal
    basic_amount: Decimal
    basic_percentage: Decimal
    hra_amount: Decimal
    hra_percentage: Decimal
    other_allowance: Decimal
    special_allowance: Decimal
    conveyance: Decimal
    medical_allowance: Decimal
    lta: Decimal
    food_coupon: Decimal
    travel_expense_max: Decimal
    is_paid_internship: bool
    has_probation: bool
    probation_months: int
    probation_extension_months: int
    mediclaim_amount: Decimal
    pa_insurance_amount: Decimal
    notice_period_probation: int
    notice_period_confirmed: int
    notice_period_termination: int
    is_active: bool


class SalaryTemplateCreate(BaseModel):
    template_code: str = Field(min_length=2, max_length=48)
    template_name: str = Field(min_length=2, max_length=96)
    category: str = Field(pattern="^(intern|trainee|permanent|contract)$")
    designation_level: int = Field(default=1, ge=1, le=10)
    ctc_annual_default: Decimal = Decimal("0")
    basic_amount: Decimal = Decimal("0")
    basic_percentage: Decimal = Decimal("50")
    hra_amount: Decimal = Decimal("0")
    hra_percentage: Decimal = Decimal("30")
    other_allowance: Decimal = Decimal("0")
    special_allowance: Decimal = Decimal("0")
    conveyance: Decimal = Decimal("0")
    medical_allowance: Decimal = Decimal("0")
    lta: Decimal = Decimal("0")
    food_coupon: Decimal = Decimal("0")
    travel_expense_max: Decimal = Decimal("0")
    is_paid_internship: bool = False
    has_probation: bool = True
    probation_months: int = Field(default=6, ge=0, le=24)
    probation_extension_months: int = Field(default=2, ge=0, le=12)
    mediclaim_amount: Decimal = Decimal("200000")
    pa_insurance_amount: Decimal = Decimal("500000")
    notice_period_probation: int = Field(default=15, ge=0, le=180)
    notice_period_confirmed: int = Field(default=30, ge=0, le=180)
    notice_period_termination: int = Field(default=7, ge=0, le=180)
    is_active: bool = True


class SalaryTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(default=None, min_length=2, max_length=96)
    category: Optional[str] = Field(
        default=None, pattern="^(intern|trainee|permanent|contract)$"
    )
    designation_level: Optional[int] = Field(default=None, ge=1, le=10)
    ctc_annual_default: Optional[Decimal] = None
    basic_amount: Optional[Decimal] = None
    basic_percentage: Optional[Decimal] = None
    hra_amount: Optional[Decimal] = None
    hra_percentage: Optional[Decimal] = None
    other_allowance: Optional[Decimal] = None
    special_allowance: Optional[Decimal] = None
    conveyance: Optional[Decimal] = None
    medical_allowance: Optional[Decimal] = None
    lta: Optional[Decimal] = None
    food_coupon: Optional[Decimal] = None
    travel_expense_max: Optional[Decimal] = None
    is_paid_internship: Optional[bool] = None
    has_probation: Optional[bool] = None
    probation_months: Optional[int] = Field(default=None, ge=0, le=24)
    probation_extension_months: Optional[int] = Field(default=None, ge=0, le=12)
    mediclaim_amount: Optional[Decimal] = None
    pa_insurance_amount: Optional[Decimal] = None
    notice_period_probation: Optional[int] = Field(default=None, ge=0, le=180)
    notice_period_confirmed: Optional[int] = Field(default=None, ge=0, le=180)
    notice_period_termination: Optional[int] = Field(default=None, ge=0, le=180)
    is_active: Optional[bool] = None


class SalaryBreakupOut(BaseModel):
    template_code: str
    template_name: str
    category: str
    is_intern: bool
    basic: int
    hra: int
    other_allowance: int
    special_allowance: int
    conveyance: int
    medical_allowance: int
    lta: int
    food_coupon: int
    gross: int
    pf_employee: int
    esic_employee: int
    professional_tax: int
    total_deductions: int
    net_salary: int
    pf_employer: int
    esic_employer: int
    total_ctc_monthly: int
    total_ctc_annual: int
    travel_expense_max: int
    is_paid_internship: bool
    notes: List[str] = []


# ── Employees ───────────────────────────────────────────────────────────
class EmployeeBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=64)
    last_name: str = Field(min_length=1, max_length=64)
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = Field(default=None, max_length=8)
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    personal_phone: Optional[str] = None
    work_location: Optional[str] = None
    employment_type: Optional[str] = "full_time"
    work_mode: Optional[str] = "office"


class EmployeeCreate(EmployeeBase):
    # Either category_code OR category_id; one is required.
    category_code: Optional[str] = None
    category_id: Optional[int] = None

    designation_id: Optional[int] = None
    department_id: Optional[int] = None
    reporting_to: Optional[int] = None

    salary_template_id: Optional[int] = None
    ctc_annual: Optional[Decimal] = None

    date_of_joining: date

    # Optional companion login user
    create_user_account: bool = False
    user_email: Optional[EmailStr] = None


class CredentialCreate(BaseModel):
    """Admin creates a mobile-app login for an existing employee."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_code: Optional[str] = Field(default=None, max_length=32)


class CredentialPasswordReset(BaseModel):
    """Admin resets the password on an employee's existing user account."""
    new_password: str = Field(min_length=8, max_length=128)


class CredentialActiveUpdate(BaseModel):
    is_active: bool


class CredentialOut(BaseModel):
    user_id: int
    email: str
    is_active: bool
    has_account: bool = True


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    personal_phone: Optional[str] = None
    photo_url: Optional[str] = None
    designation_id: Optional[int] = None
    department_id: Optional[int] = None
    reporting_to: Optional[int] = None
    work_location: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    status: Optional[str] = None


class EmployeeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: str
    first_name: str
    last_name: str
    photo_url: Optional[str] = None
    designation: Optional[DesignationOut] = None
    department: Optional[DepartmentOut] = None
    category: Optional[CategoryOut] = None
    is_on_probation: bool
    status: str
    date_of_joining: Optional[date]


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int]
    employee_code: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    blood_group: Optional[str]
    gender: Optional[str]
    marital_status: Optional[str]
    personal_email: Optional[str]
    personal_phone: Optional[str]
    photo_url: Optional[str]
    category: Optional[CategoryOut]
    designation: Optional[DesignationOut]
    department: Optional[DepartmentOut]
    reporting_to: Optional[int]
    date_of_joining: Optional[date]
    probation_end_date: Optional[date]
    confirmation_date: Optional[date]
    exit_date: Optional[date]
    salary_template: Optional[SalaryTemplateOut]
    ctc_annual: Decimal
    work_location: str
    employment_type: str
    work_mode: str
    status: str
    is_on_probation: bool
    resignation_unlocked: bool = False
    created_at: datetime


# ── Probation ───────────────────────────────────────────────────────────
class ProbationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    probation_start_date: date
    probation_end_date: date
    is_extended: bool
    extension_end_date: Optional[date]
    extension_reason: Optional[str]
    status: str
    confirmed_date: Optional[date]
    confirmation_letter_url: Optional[str]


class ProbationExtendRequest(BaseModel):
    months: int = Field(ge=1, le=12)
    reason: str = Field(min_length=5)


class ProbationConfirmRequest(BaseModel):
    confirmation_letter_url: Optional[str] = None
    note: Optional[str] = None


class ExpiringProbationItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    probation_end_date: date
    days_remaining: int


# ── Documents ───────────────────────────────────────────────────────────
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    doc_type: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: Optional[str]
    verified: bool
    expires_at: Optional[date]
    created_at: datetime


# ── Intern travel expenses ─────────────────────────────────────────────
class InternExpenseCreate(BaseModel):
    expense_date: date
    expense_type: str = Field(pattern="^(local_travel|office_commute|project_visit)$")
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None
    receipt_url: Optional[str] = None


class InternExpenseDecision(BaseModel):
    rejection_reason: Optional[str] = None


class InternExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    expense_date: date
    expense_type: str
    amount: Decimal
    receipt_url: Optional[str]
    description: Optional[str]
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    reimbursed_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime


# ── Org chart ───────────────────────────────────────────────────────────
class OrgChartNode(BaseModel):
    id: int
    employee_code: str
    name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None
    children: List["OrgChartNode"] = []


OrgChartNode.model_rebuild()

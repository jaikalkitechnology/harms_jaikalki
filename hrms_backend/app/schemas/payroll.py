from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PayrollRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    month: int
    status: str
    run_at: datetime
    finalized_at: Optional[datetime]
    total_gross: Decimal
    total_net: Decimal
    total_employer_cost: Decimal
    total_employees: int
    cycle_start_day: int = 1
    disbursed: bool = False
    disbursed_at: Optional[datetime] = None


class PayrollRunRequest(BaseModel):
    year: int = Field(ge=2024, le=2099)
    month: int = Field(ge=1, le=12)
    # 1 = calendar month; >1 = N-of-prev → (N-1)-of-this. None ⇒ use
    # each employee's own attendance_cycle_start_day.
    cycle_start_day: Optional[int] = Field(default=None, ge=1, le=28)


class PayslipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payroll_run_id: int
    employee_id: int
    year: int
    month: int
    breakup: Dict[str, Any]
    basic: Decimal
    hra: Decimal
    other_allowance: Decimal
    gross: Decimal
    pf_employee: Decimal
    esic_employee: Decimal
    professional_tax: Decimal
    tds: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    pf_employer: Decimal
    esic_employer: Decimal
    days_paid: Decimal
    days_lop: Decimal
    working_days: Decimal
    days_present: Decimal = Decimal("0")
    days_paid_leave: Decimal = Decimal("0")
    days_unpaid_leave: Decimal = Decimal("0")
    days_absent: Decimal = Decimal("0")
    days_holiday: Decimal = Decimal("0")
    days_weekoff: Decimal = Decimal("0")
    days_sandwich: Decimal = Decimal("0")
    pdf_url: Optional[str] = None
    is_final_settlement: bool = False
    on_hold: bool = False
    pf_wages: Decimal = Decimal("0")
    eps_wages: Decimal = Decimal("0")


class ReimbursementCreate(BaseModel):
    category: str = Field(
        pattern="^(travel|food|internet|phone|medical|books|other)$"
    )
    amount: Decimal = Field(gt=0)
    bill_date: date
    description: Optional[str] = None
    bill_url: Optional[str] = None


class ReimbursementDecision(BaseModel):
    rejection_reason: Optional[str] = None


class ReimbursementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    category: str
    amount: Decimal
    bill_url: Optional[str]
    bill_date: date
    description: Optional[str]
    status: str
    approver_id: Optional[int]
    approved_at: Optional[datetime]
    paid_in_run_id: Optional[int]
    rejection_reason: Optional[str]


class InvestmentDeclarationCreate(BaseModel):
    fy: str = Field(pattern=r"^\d{4}-\d{2}$")
    regime: str = Field(pattern="^(old|new)$", default="new")
    section_80c: Decimal = Decimal("0")
    section_80d: Decimal = Decimal("0")
    hra_exemption: Decimal = Decimal("0")
    home_loan_interest: Decimal = Decimal("0")
    educational_loan: Decimal = Decimal("0")
    donations_80g: Decimal = Decimal("0")
    other: Optional[dict] = None


class InvestmentDeclarationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    fy: str
    regime: str
    locked_at: Optional[datetime]
    section_80c: Decimal
    section_80d: Decimal
    hra_exemption: Decimal
    home_loan_interest: Decimal
    educational_loan: Decimal
    donations_80g: Decimal
    other: Optional[dict] = None


class GeneratedDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    doc_type: str
    letter_number: Optional[str]
    file_url: str
    created_at: datetime


class BankFileExportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payroll_run_id: int
    file_url: str
    bank_format: str
    total_amount: Decimal
    total_employees: int


class PayrollRunDetail(BaseModel):
    run: PayrollRunOut
    payslips: List[PayslipOut]


# ── PF wage ceiling register ──────────────────────────────────────────
class PfCeilingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cap_amount: Decimal
    eps_cap_amount: Decimal
    effective_from: date
    recorded_on: date
    mid_month_mode: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    # Derived fields filled in by the API.
    applies_from: Optional[date] = None
    status: Optional[str] = None  # past | active | scheduled
    locked: bool = False


class PfCeilingCreate(BaseModel):
    cap_amount: Decimal = Field(gt=0)
    eps_cap_amount: Optional[Decimal] = Field(default=None, gt=0)
    effective_from: date
    recorded_on: Optional[date] = None
    mid_month_mode: str = Field(
        default="day_weighted", pattern="^(day_weighted|whole_month|next_month)$"
    )
    reference: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class PfCeilingUpdate(BaseModel):
    cap_amount: Optional[Decimal] = Field(default=None, gt=0)
    eps_cap_amount: Optional[Decimal] = Field(default=None, gt=0)
    effective_from: Optional[date] = None
    recorded_on: Optional[date] = None
    mid_month_mode: Optional[str] = Field(
        default=None, pattern="^(day_weighted|whole_month|next_month)$"
    )
    reference: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class PfCapCurrentOut(BaseModel):
    pf_cap: Decimal
    eps_cap: Decimal
    as_of: date
    next_change: Optional[PfCeilingOut] = None


class PfCeilingImpactRow(BaseModel):
    employee_id: int
    employee_code: str
    name: str
    basic: int
    old_pf_employee: int
    new_pf_employee: int
    old_pf_employer: int
    new_pf_employer: int
    old_gross: int
    new_gross: int
    old_net: int
    new_net: int
    net_change: int
    absorb_ctc_annual: int  # CTC needed to keep gross unchanged


class PfCeilingImpactOut(BaseModel):
    ceiling_id: int
    old_cap: Decimal
    new_cap: Decimal
    first_full_month: str  # e.g. "2026-10"
    effective_month_cap: Decimal  # day-weighted cap for the effective month
    rows: List[PfCeilingImpactRow]


class PfCeilingAbsorbRequest(BaseModel):
    employee_ids: List[int]
    effective_date: Optional[date] = None
    reason: str = "PF wage ceiling change — company absorbs employer PF increase"


class PayrollPolicyOut(BaseModel):
    division_basis: str


class PayrollPolicyUpdate(BaseModel):
    division_basis: str = Field(pattern="^(calendar_days|working_days|fixed_30)$")

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SalaryRevisionPropose(BaseModel):
    employee_id: int
    new_ctc_annual: Decimal = Field(gt=0)
    effective_date: date
    reason: str = Field(
        default="annual_review",
        pattern="^(annual_review|promotion|market_correction|"
        "retention|role_change|other)$",
    )
    new_salary_template_id: Optional[int] = None
    new_designation_id: Optional[int] = None
    notes: Optional[str] = None


class SalaryRevisionRejectBody(BaseModel):
    reason: Optional[str] = None


class SalaryRevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    proposed_by: Optional[int]
    reason: str
    previous_ctc_annual: Decimal
    new_ctc_annual: Decimal
    increment_pct: Decimal
    new_salary_template_id: Optional[int]
    new_designation_id: Optional[int]
    effective_date: date
    notes: Optional[str]
    breakup_snapshot: Optional[dict] = None
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    applied_at: Optional[datetime]
    increment_letter_url: Optional[str]
    created_at: datetime

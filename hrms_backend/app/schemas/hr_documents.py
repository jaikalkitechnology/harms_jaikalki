from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.hr_documents import LETTER_TYPES, POLICY_CATEGORIES

LETTER_TYPE_RE = "^(" + "|".join(LETTER_TYPES) + ")$"
POLICY_CATEGORY_RE = "^(" + "|".join(POLICY_CATEGORIES) + ")$"


# ── Letterhead ───────────────────────────────────────────────────────
class LetterheadSettings(BaseModel):
    company_name: str = ""
    cin: str = ""
    gst: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    regd_office: str = ""
    corporate_office: str = ""
    footer_note: str = ""
    show_watermark: bool = True
    show_corner_accents: bool = True


class LetterheadOut(LetterheadSettings):
    has_custom_logo: bool = False


class LetterheadUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, max_length=120)
    cin: Optional[str] = Field(default=None, max_length=40)
    gst: Optional[str] = Field(default=None, max_length=40)
    phone: Optional[str] = Field(default=None, max_length=60)
    email: Optional[str] = Field(default=None, max_length=120)
    website: Optional[str] = Field(default=None, max_length=120)
    regd_office: Optional[str] = Field(default=None, max_length=300)
    corporate_office: Optional[str] = Field(default=None, max_length=400)
    footer_note: Optional[str] = Field(default=None, max_length=160)
    show_watermark: Optional[bool] = None
    show_corner_accents: Optional[bool] = None


# ── Employee letters ─────────────────────────────────────────────────
class EmployeeLetterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    letter_type: str
    title: str
    letter_number: Optional[str] = None
    issued_on: date
    source: str
    template_id: Optional[int] = None
    file_name: str
    mime_type: str
    file_size: Optional[int] = None
    visible_to_employee: bool
    notes: Optional[str] = None
    issued_by: Optional[int] = None
    created_at: Optional[datetime] = None


class EmployeeLetterIssue(BaseModel):
    """Create a letter from a template and keep it on file."""

    letter_type: Optional[str] = Field(default=None, pattern=LETTER_TYPE_RE)
    title: Optional[str] = Field(default=None, max_length=200)
    letter_no: Optional[str] = Field(default=None, max_length=64)
    on_date: Optional[date] = None
    last_working_date: Optional[str] = None
    ctc_amount: Optional[str] = None
    ctc_amount_words: Optional[str] = None
    overrides: Optional[dict] = None
    visible_to_employee: bool = True
    notes: Optional[str] = Field(default=None, max_length=500)


class EmployeeLetterUpdate(BaseModel):
    letter_type: Optional[str] = Field(default=None, pattern=LETTER_TYPE_RE)
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    letter_number: Optional[str] = Field(default=None, max_length=64)
    issued_on: Optional[date] = None
    visible_to_employee: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=500)


# ── Company policies ─────────────────────────────────────────────────
class CompanyPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    description: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[date] = None
    file_name: str
    mime_type: str
    file_size: Optional[int] = None
    is_published: bool
    requires_acknowledgement: bool = True
    revision: int = 1
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # For the signed-in employee: when they accepted this revision.
    my_acknowledged_at: Optional[datetime] = None
    # For HR: how many current employees have / haven't accepted it.
    acknowledged_count: Optional[int] = None
    pending_count: Optional[int] = None


class CompanyPolicyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    category: Optional[str] = Field(default=None, pattern=POLICY_CATEGORY_RE)
    description: Optional[str] = Field(default=None, max_length=4000)
    version: Optional[str] = Field(default=None, max_length=32)
    effective_date: Optional[date] = None
    is_published: Optional[bool] = None
    requires_acknowledgement: Optional[bool] = None


class PolicyAckRow(BaseModel):
    employee_id: int
    employee_code: str
    name: str
    department: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class PolicyAckReport(BaseModel):
    policy_id: int
    revision: int
    acknowledged: list[PolicyAckRow]
    pending: list[PolicyAckRow]

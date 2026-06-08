from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LetterTemplateBase(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(default="other")
    subject: Optional[str] = None
    body: str
    is_active: bool = True
    placeholders: Optional[str] = None


class LetterTemplateCreate(LetterTemplateBase):
    pass


class LetterTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    category: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None
    placeholders: Optional[str] = None


class LetterTemplateOut(LetterTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class LetterGenerateOptions(BaseModel):
    """Optional per-render overrides — anything in ``overrides`` wins
    over the value resolved from the employee record."""

    letter_no: Optional[str] = None
    on_date: Optional[str] = None  # ISO date; defaults to today
    last_working_date: Optional[str] = None
    ctc_amount: Optional[str] = None
    ctc_amount_words: Optional[str] = None
    overrides: Optional[dict] = None


class LetterPlaceholderHint(BaseModel):
    key: str
    description: str


COMMON_PLACEHOLDERS: List[LetterPlaceholderHint] = [
    LetterPlaceholderHint(key="full_name", description="Employee full name"),
    LetterPlaceholderHint(key="first_name", description="Employee first name"),
    LetterPlaceholderHint(key="last_name", description="Employee last name"),
    LetterPlaceholderHint(key="salutation", description="Mr./Ms./Mr./Ms."),
    LetterPlaceholderHint(key="employee_code", description="Employee code (e.g. JKT001)"),
    LetterPlaceholderHint(key="designation", description="Designation / title"),
    LetterPlaceholderHint(key="department", description="Department name"),
    LetterPlaceholderHint(key="date_of_joining", description="Date of joining"),
    LetterPlaceholderHint(key="last_working_date", description="Last working date (override)"),
    LetterPlaceholderHint(key="email", description="Personal / work email"),
    LetterPlaceholderHint(key="phone", description="Personal phone"),
    LetterPlaceholderHint(key="address", description="Address (override)"),
    LetterPlaceholderHint(key="ctc_amount", description="CTC amount (figures)"),
    LetterPlaceholderHint(key="ctc_amount_words", description="CTC amount in words"),
    LetterPlaceholderHint(key="date", description="Letter date (defaults to today)"),
    LetterPlaceholderHint(key="letter_no", description="Letter reference number"),
]

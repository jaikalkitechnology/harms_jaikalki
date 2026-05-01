from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DwpFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    label: str
    help_text: Optional[str] = None
    field_type: str
    is_required: bool
    options: Optional[list] = None
    display_order: int


class DwpTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: Optional[str] = None
    department_id: Optional[int] = None
    type: str
    is_active: bool
    fields: List[DwpFieldOut] = []


class DwpTemplateWithPrefill(BaseModel):
    template: DwpTemplateOut
    prefill: Dict[str, Any] = Field(default_factory=dict)
    linked_morning_id: Optional[int] = None
    streak_days: int = 0


class DwpSubmitRequest(BaseModel):
    template_id: int
    fields: Dict[str, Any]
    total_hours: Optional[Decimal] = None
    mood_rating: Optional[int] = Field(default=None, ge=1, le=5)
    on_date: Optional[date] = None


class DwpSubmissionFieldOut(BaseModel):
    field_key: str
    value: Optional[str] = None
    file_url: Optional[str] = None


class DwpCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    submission_id: int
    commented_by: int
    comment: str
    is_kudos: bool
    created_at: datetime


class DwpSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    template_id: int
    type: str
    date: date
    submitted_at: datetime
    total_hours: Optional[Decimal] = None
    mood_rating: Optional[int] = None
    linked_morning_id: Optional[int] = None
    fields: List[DwpSubmissionFieldOut] = []
    comments: List[DwpCommentOut] = []


class DwpTeamSubmissionItem(BaseModel):
    submission: DwpSubmissionOut
    employee_code: str
    employee_full_name: str


class DwpCommentCreate(BaseModel):
    comment: str = Field(min_length=1)
    is_kudos: bool = False


class DwpStreakOut(BaseModel):
    employee_id: int
    streak_days: int
    last_submission_date: Optional[date]

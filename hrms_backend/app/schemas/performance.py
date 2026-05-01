from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Cycles ──────────────────────────────────────────────────────────
class CycleCreate(BaseModel):
    code: str
    name: str
    cycle_type: str = Field(
        default="quarterly",
        pattern="^(quarterly|half_yearly|annual|monthly)$",
    )
    period_start: date
    period_end: date
    self_review_due: Optional[date] = None
    manager_review_due: Optional[date] = None
    calibration_due: Optional[date] = None


class CycleStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(draft|open|review|calibration|closed)$"
    )


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    cycle_type: str
    period_start: date
    period_end: date
    self_review_due: Optional[date]
    manager_review_due: Optional[date]
    calibration_due: Optional[date]
    status: str


# ── Goals ───────────────────────────────────────────────────────────
class GoalCreate(BaseModel):
    employee_id: Optional[int] = None
    cycle_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    metric: Optional[str] = None
    target_value: Optional[str] = None
    weight_pct: int = Field(default=100, ge=0, le=100)
    category: str = Field(
        default="business",
        pattern="^(business|people|growth|operational|personal)$",
    )
    due_date: Optional[date] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    metric: Optional[str] = None
    target_value: Optional[str] = None
    weight_pct: Optional[int] = Field(default=None, ge=0, le=100)
    progress_pct: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[str] = Field(
        default=None,
        pattern="^(draft|active|at_risk|achieved|missed|cancelled)$",
    )
    due_date: Optional[date] = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    cycle_id: Optional[int]
    title: str
    description: Optional[str]
    metric: Optional[str]
    target_value: Optional[str]
    weight_pct: int
    progress_pct: int
    category: str
    status: str
    due_date: Optional[date]


# ── Reviews ─────────────────────────────────────────────────────────
class ReviewSubmit(BaseModel):
    overall_rating: Optional[Decimal] = Field(default=None, ge=1, le=5)
    achievements: Optional[str] = None
    improvement_areas: Optional[str] = None
    recommendations: Optional[str] = None
    increment_recommendation_pct: Optional[int] = Field(
        default=None, ge=0, le=100
    )
    competencies: Optional[dict] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cycle_id: int
    employee_id: int
    review_type: str
    reviewer_id: Optional[int]
    overall_rating: Optional[Decimal]
    achievements: Optional[str]
    improvement_areas: Optional[str]
    recommendations: Optional[str]
    increment_recommendation_pct: Optional[int]
    competencies: Optional[dict] = None
    status: str
    submitted_at: Optional[datetime]
    acknowledged_at: Optional[datetime]


# ── 360 Feedback ────────────────────────────────────────────────────
class FeedbackRequestCreate(BaseModel):
    cycle_id: Optional[int] = None
    subject_employee_id: int
    reviewer_employee_ids: List[int] = Field(min_length=1)
    relation: str = Field(
        default="peer",
        pattern="^(peer|reportee|manager|cross_functional)$",
    )
    is_anonymous: bool = True


class FeedbackRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cycle_id: Optional[int]
    subject_employee_id: int
    reviewer_employee_id: int
    relation: str
    is_anonymous: bool
    status: str


class FeedbackResponseSubmit(BaseModel):
    overall_rating: Decimal = Field(ge=1, le=5)
    strengths: Optional[str] = None
    improvement_areas: Optional[str] = None
    competencies: Optional[dict] = None


class FeedbackResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: int
    overall_rating: Optional[Decimal]
    strengths: Optional[str]
    improvement_areas: Optional[str]
    competencies: Optional[dict] = None
    submitted_at: datetime


class FeedbackAggregate(BaseModel):
    subject_employee_id: int
    response_count: int
    avg_rating: float
    competency_averages: dict
    anonymous_strengths: List[str]
    anonymous_improvements: List[str]


# ── 1-on-1 ──────────────────────────────────────────────────────────
class OneOnOneCreate(BaseModel):
    employee_id: int
    meeting_date: date
    agenda: Optional[str] = None
    discussion_notes: Optional[str] = None
    action_items: Optional[List[dict]] = None
    visibility: str = Field(
        default="shared", pattern="^(manager_only|shared|private)$"
    )


class OneOnOneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    manager_id: int
    meeting_date: date
    agenda: Optional[str]
    discussion_notes: Optional[str]
    action_items: Optional[list] = None
    visibility: str
    created_at: datetime

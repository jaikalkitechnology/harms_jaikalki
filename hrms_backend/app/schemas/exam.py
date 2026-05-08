from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Question bank ────────────────────────────────────────────────────
class QuestionOptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False
    sort_order: int = 0


class QuestionOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    option_text: str
    is_correct: bool
    sort_order: int


class QuestionOptionPublic(BaseModel):
    """Option without is_correct — used in candidate-facing views."""

    id: int
    option_text: str
    sort_order: int


class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = Field(
        default="single_choice",
        pattern="^(single_choice|multiple_choice|true_false|fill_blank|"
        "match_pairs|short_answer)$",
    )
    department_id: Optional[int] = None
    course_id: Optional[int] = None
    topic: Optional[str] = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    language: str = "en"
    marks: int = Field(default=1, ge=1, le=20)
    time_seconds: int = Field(default=60, ge=10, le=900)
    explanation: Optional[str] = None
    options: List[QuestionOptionCreate] = []


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_text: str
    question_type: str
    department_id: Optional[int]
    course_id: Optional[int] = None
    topic: Optional[str]
    difficulty: str
    language: str
    marks: int
    time_seconds: int
    explanation: Optional[str]
    status: str
    options: List[QuestionOptionOut] = []


class QuestionPublic(BaseModel):
    """Public/candidate-facing question without correctness leaking."""

    id: int
    question_text: str
    question_type: str
    marks: int
    time_seconds: int
    options: List[QuestionOptionPublic] = []


# ── Exams ────────────────────────────────────────────────────────────
class ExamCreate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    course_id: Optional[int] = None
    department_id: Optional[int] = None
    exam_type: str = Field(
        default="assessment",
        pattern="^(practice|assessment|certification|mandatory)$",
    )
    total_questions: int = Field(default=10, ge=1, le=200)
    time_limit_minutes: int = Field(default=30, ge=1, le=480)
    passing_percentage: int = Field(default=60, ge=0, le=100)
    question_selection: str = Field(default="fixed", pattern="^(fixed|random)$")
    shuffle_questions: bool = True
    shuffle_options: bool = True
    attempts_allowed: int = Field(default=3, ge=1, le=20)
    cooldown_hours: int = Field(default=24, ge=0, le=720)
    negative_marking: bool = False
    validity_months: Optional[int] = None
    question_ids: List[int] = []


class ExamPublishUpdate(BaseModel):
    is_published: bool


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    course_id: Optional[int] = None
    department_id: Optional[int] = None
    exam_type: Optional[str] = Field(
        default=None,
        pattern="^(practice|assessment|certification|mandatory)$",
    )
    total_questions: Optional[int] = Field(default=None, ge=1, le=200)
    time_limit_minutes: Optional[int] = Field(default=None, ge=1, le=480)
    passing_percentage: Optional[int] = Field(default=None, ge=0, le=100)
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    attempts_allowed: Optional[int] = Field(default=None, ge=1, le=20)
    cooldown_hours: Optional[int] = Field(default=None, ge=0, le=720)
    negative_marking: Optional[bool] = None
    validity_months: Optional[int] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = Field(
        default=None,
        pattern="^(single_choice|multiple_choice|true_false|fill_blank|"
        "match_pairs|short_answer)$",
    )
    department_id: Optional[int] = None
    course_id: Optional[int] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = Field(default=None, pattern="^(easy|medium|hard)$")
    language: Optional[str] = None
    marks: Optional[int] = Field(default=None, ge=1, le=20)
    time_seconds: Optional[int] = Field(default=None, ge=10, le=900)
    explanation: Optional[str] = None
    status: Optional[str] = Field(
        default=None, pattern="^(draft|active|retired)$"
    )


class ExamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    description: Optional[str]
    course_id: Optional[int]
    exam_type: str
    total_questions: int
    time_limit_minutes: int
    passing_percentage: int
    attempts_allowed: int
    is_published: bool


class ExamOut(ExamSummary):
    department_id: Optional[int]
    question_selection: str
    shuffle_questions: bool
    shuffle_options: bool
    cooldown_hours: int
    negative_marking: bool
    validity_months: Optional[int]


# ── Attempts ─────────────────────────────────────────────────────────
class StartAttemptResponse(BaseModel):
    attempt_id: int
    started_at: datetime
    time_limit_minutes: int
    questions: List[QuestionPublic]
    cheating_threshold: int = 3


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_ids: Optional[List[int]] = None
    text_answer: Optional[str] = None
    time_taken_seconds: int = Field(default=0, ge=0)


class FlagSubmit(BaseModel):
    flag_type: str = Field(
        pattern="^(tab_switch|copy_attempt|paste_attempt|fullscreen_exit|"
        "right_click|multiple_devices|other)$"
    )
    note: Optional[str] = None


class AttemptSubmitRequest(BaseModel):
    answers: List[AnswerSubmit] = []
    cheating_flags: List[dict] = []


class AttemptResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    exam_id: int
    employee_id: int
    started_at: datetime
    submitted_at: Optional[datetime]
    time_taken_seconds: int
    total_score: int
    max_score: int
    percentage: Decimal
    status: str
    passed: bool
    attempt_number: int
    cheating_flags: Optional[list] = None


class AttemptDetail(AttemptResult):
    answers: List["AnswerOut"] = []


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    selected_option_ids: Optional[list] = None
    text_answer: Optional[str]
    is_correct: bool
    marks_awarded: int
    time_taken_seconds: int


_CERTIFICATE_TYPES_RE = (
    "^(achievement|appreciation|completion|participation|excellence|training|custom)$"
)


# ── Certificates ─────────────────────────────────────────────────────
class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    certificate_number: str
    employee_id: int
    course_id: Optional[int]
    exam_attempt_id: Optional[int]
    title: str
    certificate_type: Optional[str] = None
    body_text: Optional[str] = None
    issued_date: date
    expiry_date: Optional[date]
    score_percentage: Optional[Decimal]
    pdf_url: Optional[str]
    is_revoked: bool
    revoked_reason: Optional[str] = None


class CertificateCreate(BaseModel):
    employee_id: int
    title: str = Field(min_length=2, max_length=200)
    certificate_type: Optional[str] = Field(
        default="achievement", pattern=_CERTIFICATE_TYPES_RE
    )
    body_text: Optional[str] = Field(default=None, max_length=1000)
    course_id: Optional[int] = None
    exam_attempt_id: Optional[int] = None
    issued_date: Optional[date] = None
    expiry_date: Optional[date] = None
    score_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)


class CertificateUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    certificate_type: Optional[str] = Field(
        default=None, pattern=_CERTIFICATE_TYPES_RE
    )
    body_text: Optional[str] = Field(default=None, max_length=1000)
    issued_date: Optional[date] = None
    expiry_date: Optional[date] = None
    score_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    course_id: Optional[int] = None


class CertificateRevoke(BaseModel):
    reason: str = Field(min_length=2, max_length=255)


class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate_number: str
    employee_name: Optional[str] = None
    title: Optional[str] = None
    issued_date: Optional[date] = None
    expiry_date: Optional[date] = None
    score_percentage: Optional[Decimal] = None
    is_revoked: bool = False
    revoked_reason: Optional[str] = None


AttemptDetail.model_rebuild()

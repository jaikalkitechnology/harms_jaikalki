from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TrainerProfileCreate(BaseModel):
    employee_id: Optional[int] = None
    is_external: bool = False
    full_name: str
    bio: Optional[str] = None
    headline: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    languages: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    years_experience: int = Field(default=0, ge=0, le=80)
    hourly_rate: Optional[Decimal] = None


class TrainerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    headline: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    languages: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    years_experience: Optional[int] = Field(default=None, ge=0, le=80)
    hourly_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None


class TrainerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: Optional[int]
    is_external: bool
    full_name: str
    bio: Optional[str]
    headline: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    profile_photo_url: Optional[str]
    languages: Optional[list] = None
    specializations: Optional[list] = None
    years_experience: int
    hourly_rate: Optional[Decimal]
    rating_average: Decimal
    sessions_completed: int
    is_active: bool


class TrainingSessionCreate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    trainer_id: int
    course_id: Optional[int] = None
    department_id: Optional[int] = None
    session_type: str = Field(
        default="virtual", pattern="^(in_person|virtual|hybrid|self_paced)$"
    )
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str = "Asia/Kolkata"
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    capacity: int = Field(default=30, ge=1, le=2000)


class TrainingSessionStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(scheduled|open_for_registration|in_progress|completed|cancelled)$"
    )


class TrainingSessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    trainer_id: Optional[int] = None
    course_id: Optional[int] = None
    department_id: Optional[int] = None
    session_type: Optional[str] = Field(
        default=None, pattern="^(in_person|virtual|hybrid|self_paced)$"
    )
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    capacity: Optional[int] = Field(default=None, ge=1, le=2000)


class TrainingSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    description: Optional[str]
    trainer_id: int
    course_id: Optional[int]
    department_id: Optional[int]
    session_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str
    location: Optional[str]
    meeting_url: Optional[str]
    capacity: int
    qr_token: Optional[str]
    recording_url: Optional[str]
    status: str
    participants_count: int = 0


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    employee_id: int
    registered_at: datetime
    checked_in_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str


class CheckInRequest(BaseModel):
    qr_token: str


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review_text: Optional[str] = None
    is_anonymous: bool = False


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trainer_id: int
    session_id: Optional[int]
    employee_id: int
    rating: int
    review_text: Optional[str]
    is_anonymous: bool
    created_at: datetime


class TrainerAnalytics(BaseModel):
    trainer_id: int
    full_name: str
    sessions_completed: int
    upcoming_sessions: int
    total_participants: int
    avg_rating: float
    review_count: int
    attendance_rate: float

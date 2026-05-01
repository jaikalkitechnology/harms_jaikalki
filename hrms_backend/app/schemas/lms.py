from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Lessons ──────────────────────────────────────────────────────────
class LessonCreate(BaseModel):
    title: str
    content_type: str = Field(
        default="article",
        pattern="^(video|pdf|article|external_link|image|audio|quiz|scorm|"
        "live_session)$",
    )
    content_url: Optional[str] = None
    article_body: Optional[str] = None
    duration_minutes: int = Field(default=10, ge=1, le=480)
    sort_order: int = 0
    points: int = 1


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    module_id: int
    title: str
    content_type: str
    content_url: Optional[str]
    article_body: Optional[str]
    duration_minutes: int
    sort_order: int
    points: int


# ── Modules ──────────────────────────────────────────────────────────
class ModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    sort_order: int = 0
    lessons: List[LessonCreate] = []


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    title: str
    description: Optional[str]
    sort_order: int
    lessons: List[LessonOut] = []


# ── Courses ──────────────────────────────────────────────────────────
class CourseCreate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    category: str = Field(
        default="other",
        pattern="^(onboarding|compliance|technical|leadership|soft_skills|"
        "product|other)$",
    )
    department_id: Optional[int] = None
    difficulty: str = Field(
        default="beginner", pattern="^(beginner|intermediate|advanced)$"
    )
    estimated_hours: int = Field(default=1, ge=1, le=200)
    thumbnail_url: Optional[str] = None
    is_mandatory: bool = False
    validity_months: Optional[int] = Field(default=None, ge=1, le=120)
    points: int = Field(default=10, ge=0)
    modules: List[ModuleCreate] = []


class CoursePublishUpdate(BaseModel):
    is_published: bool


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    description: Optional[str]
    category: str
    department_id: Optional[int]
    difficulty: str
    estimated_hours: int
    thumbnail_url: Optional[str]
    is_mandatory: bool
    validity_months: Optional[int]
    is_published: bool
    points: int
    modules: List[ModuleOut] = []


class CourseSummary(BaseModel):
    """Card-friendly summary without lessons."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    description: Optional[str]
    category: str
    difficulty: str
    estimated_hours: int
    is_mandatory: bool
    points: int
    thumbnail_url: Optional[str]


# ── Enrollment / progress ───────────────────────────────────────────
class EnrollmentCreate(BaseModel):
    course_id: int
    employee_id: Optional[int] = None
    due_date: Optional[date] = None


class LessonProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    status: str
    time_spent_seconds: int
    completed_at: Optional[datetime]
    notes: Optional[str]


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    course_id: int
    enrolled_at: datetime
    due_date: Optional[date]
    status: str
    progress_percentage: int
    completed_at: Optional[datetime]
    score: Optional[int]
    progress: List[LessonProgressOut] = []


class LessonCompleteRequest(BaseModel):
    time_spent_seconds: int = Field(default=0, ge=0)
    notes: Optional[str] = None


# ── Badges & stats ──────────────────────────────────────────────────
class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    points_required: int
    courses_required: int
    streak_days_required: int
    tier: str


class EmployeeBadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    badge_id: int
    awarded_at: datetime


class LearningStatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    employee_id: int
    points: int
    courses_completed: int
    lessons_completed: int
    streak_days: int
    last_activity_date: Optional[date]
    level: str
    badges: List[BadgeOut] = []


class LeaderboardEntry(BaseModel):
    employee_id: int
    employee_code: str
    name: str
    points: int
    courses_completed: int
    level: str
    streak_days: int

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Notifications ───────────────────────────────────────────────────
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel: str
    type: str
    title: str
    body: Optional[str]
    data: Optional[dict] = None
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    status: str
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int


class NotificationBroadcast(BaseModel):
    """Admin-initiated push to many users."""

    audience: str = Field(pattern="^(all|role|department|users)$")
    title: str = Field(min_length=1, max_length=200)
    body: Optional[str] = Field(default=None, max_length=2000)
    type: str = Field(default="broadcast", max_length=64)
    data: Optional[dict] = None
    send_push: bool = True
    # audience-specific knobs
    user_ids: Optional[List[int]] = None
    role_codes: Optional[List[str]] = None
    department_id: Optional[int] = None


class BroadcastResult(BaseModel):
    queued: int
    sent: int


class DeviceTokenRegister(BaseModel):
    platform: str = Field(pattern="^(android|ios|web)$")
    token: str


class DeviceTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform: str
    is_active: bool


# ─── Audit ───────────────────────────────────────────────────────────
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_user_id: Optional[int]
    actor_label: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    request_id: Optional[str]
    ip: Optional[str]
    user_agent: Optional[str]
    method: Optional[str]
    path: Optional[str]
    status_code: Optional[int]
    payload: Optional[dict] = None
    occurred_at: datetime


# ─── Resignation ─────────────────────────────────────────────────────
class ResignationCreate(BaseModel):
    proposed_last_working_day: date
    reason: Optional[str] = None
    notice_period_days: int = Field(default=60, ge=0, le=180)


class ResignationDecision(BaseModel):
    accept: bool
    comment: Optional[str] = None
    actual_last_working_day: Optional[date] = None


class ResignationNdcUpdate(BaseModel):
    updates: dict


class ResignationSettle(BaseModel):
    final_settlement_amount: int = Field(ge=0)
    exit_interview_notes: Optional[str] = None


class ResignationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    requested_at: datetime
    proposed_last_working_day: date
    actual_last_working_day: Optional[date]
    reason: Optional[str]
    status: str
    separation_type: str = "resignation"
    manager_decision_at: Optional[datetime]
    manager_decision_by: Optional[int]
    manager_comment: Optional[str]
    notice_period_days: int
    ndc_checklist: Optional[dict] = None
    hr_cleared_at: Optional[datetime]
    final_settlement_amount: Optional[int]
    final_settled_at: Optional[datetime]
    exit_interview_notes: Optional[str]
    documents: Optional[list] = None


class AdminSeparationCreate(BaseModel):
    """Admin-initiated resignation or termination on behalf of an
    employee. Auto-approves at ``in_notice`` (or ``accepted`` when the
    proposed last working day is today / in the past)."""

    employee_id: int
    separation_type: str = Field(default="resignation", pattern="^(resignation|termination)$")
    proposed_last_working_day: date
    reason: Optional[str] = None
    notice_period_days: int = Field(default=30, ge=0, le=180)
    manager_comment: Optional[str] = None


class SeparationEmailRequest(BaseModel):
    """Send the generated letter to the employee (and optional CCs)."""

    to: Optional[str] = None  # override; defaults to employee email
    cc: Optional[list[str]] = None
    subject: Optional[str] = None
    body: Optional[str] = None


# ─── Bulk import ─────────────────────────────────────────────────────
class BulkImportError(BaseModel):
    row: int
    error: str


class BulkImportResult(BaseModel):
    total: int
    created: int
    errors: List[BulkImportError]

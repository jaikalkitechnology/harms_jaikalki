from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AccusedIn(BaseModel):
    name: str
    employee_id: Optional[int] = None
    relationship_type: Optional[str] = None


class WitnessIn(BaseModel):
    name: str
    statement: Optional[str] = None
    is_anonymous: bool = False


class EvidenceIn(BaseModel):
    file_url: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_hash: Optional[str] = None


class ComplaintCreate(BaseModel):
    complaint_type: str
    privacy_level: str = Field(default="confidential")
    severity: str = Field(default="medium")
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    desired_outcome: Optional[str] = None
    incident_date: Optional[date] = None
    incident_location: Optional[str] = None
    accused: List[AccusedIn] = []
    witnesses: List[WitnessIn] = []
    evidence: List[EvidenceIn] = []


class AccusedOut(BaseModel):
    id: int
    name: str
    accused_employee_id: Optional[int] = None
    relationship_type: Optional[str] = None


class WitnessOut(BaseModel):
    id: int
    name: Optional[str] = None
    statement: Optional[str] = None
    is_anonymous: bool


class EvidenceOut(BaseModel):
    id: int
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_hash: Optional[str] = None


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action_type: str
    action_date: datetime
    taken_by: Optional[int]
    notes: Optional[str] = None


class TimelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    event_description: Optional[str]
    event_date: datetime
    done_by: Optional[int]


class AccessLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int]
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None


class ComplaintListItem(BaseModel):
    id: int
    ticket_number: str
    complaint_type: str
    privacy_level: str
    severity: str
    status: str
    subject: str
    submitted_at: datetime
    deadline_at: Optional[datetime] = None
    is_anonymous: bool


class ComplaintDetail(BaseModel):
    id: int
    ticket_number: str
    complaint_type: str
    privacy_level: str
    severity: str
    status: str
    subject: str
    description: Optional[str] = None
    desired_outcome: Optional[str] = None
    incident_date: Optional[date] = None
    incident_location: Optional[str] = None
    submitted_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    assigned_to: Optional[int] = None
    complainant_employee_id: Optional[int] = None
    accused: List[AccusedOut] = []
    witnesses: List[WitnessOut] = []
    evidence: List[EvidenceOut] = []
    actions: List[ActionOut] = []
    timeline: List[TimelineOut] = []
    access_log: List[AccessLogOut] = []


class AssignRequest(BaseModel):
    user_id: int


class ActionCreate(BaseModel):
    action_type: str
    notes: Optional[str] = None


class ResolveRequest(BaseModel):
    notes: Optional[str] = None
    action_type: str = "case_closed"


class WithdrawRequest(BaseModel):
    reason: Optional[str] = None


class IccMemberCreate(BaseModel):
    member_name: str
    user_id: Optional[int] = None
    role: str
    gender: Optional[str] = None
    is_external: bool = False
    term_start: date
    term_end: Optional[date] = None
    contact: Optional[str] = None


class IccMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_name: str
    user_id: Optional[int]
    role: str
    gender: Optional[str]
    is_external: bool
    term_start: date
    term_end: Optional[date]
    is_active: bool
    contact: Optional[str]


class IccComplianceStatus(BaseModel):
    compliant: bool
    reasons: List[str]
    member_count: int
    women_count: int
    external_count: int
    has_presiding_officer: bool


class PoshAnnualReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    total_complaints: int
    resolved: int
    pending: int
    actions_taken_json: Optional[dict] = None
    generated_at: datetime


class RetaliationFlagCreate(BaseModel):
    employee_id: int
    flag_type: str
    description: Optional[str] = None
    complaint_id: Optional[int] = None


class RetaliationFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    complaint_id: Optional[int]
    employee_id: int
    flag_type: str
    detected_at: datetime
    description: Optional[str]
    resolved: bool

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Templates ─────────────────────────────────────────────────────────
class TemplateField(BaseModel):
    """A single field in a verification template."""

    key: str
    label: str
    field_type: str = Field(
        pattern="^(text|number|date|dropdown|checkbox|photo|signature|"
        "address|phone|email|textarea)$"
    )
    required: bool = False
    options: Optional[List[str]] = None
    help_text: Optional[str] = None


class PhotoRequirement(BaseModel):
    key: str
    label: str
    required: bool = True


class TemplateCreate(BaseModel):
    code: str
    name: str
    type: str = Field(
        pattern="^(address|employment|document|business|education|criminal|bank|other)$"
    )
    description: Optional[str] = None
    fields: List[TemplateField]
    photo_requirements: Optional[List[PhotoRequirement]] = None
    signature_required: bool = False
    sla_hours: int = Field(default=48, ge=1, le=720)


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    type: str
    description: Optional[str]
    fields: list
    photo_requirements: Optional[list] = None
    signature_required: bool
    sla_hours: int
    is_active: bool


# ── Verifications ─────────────────────────────────────────────────────
class VerificationCreate(BaseModel):
    template_id: int
    subject_name: str
    subject_data: dict
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    requested_by_org: Optional[str] = None
    assigned_to: Optional[int] = None


class VerificationSubmit(BaseModel):
    form_data: dict
    photos: Optional[List[str]] = None
    signature_url: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    result: str = Field(pattern="^(positive|negative|unable_to_verify|partial)$")
    remarks: Optional[str] = None


class VerificationAuditDecision(BaseModel):
    audit_status: str = Field(pattern="^(approved|rejected|rework)$")
    audit_comments: Optional[str] = None


class FraudFlagCreate(BaseModel):
    flag_type: str = Field(
        pattern="^(duplicate_subject|geo_anomaly|photo_tampered|"
        "form_inconsistent|missing_documents|suspicious_pattern|other)$"
    )
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    notes: Optional[str] = None


class FraudFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    verification_id: int
    flag_type: str
    severity: str
    detected_by: str
    notes: Optional[str]
    detected_at: datetime


class VerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_number: str
    template_id: int
    type: str
    subject_name: str
    subject_data: dict
    address: Optional[str]
    contact_phone: Optional[str]
    requested_by_org: Optional[str]
    assigned_to: Optional[int]
    assigned_at: datetime
    deadline_at: Optional[datetime]
    status: str
    form_data: Optional[dict] = None
    photos: Optional[list] = None
    signature_url: Optional[str]
    geo_lat: Optional[str]
    geo_lng: Optional[str]
    submitted_at: Optional[datetime]
    result: Optional[str]
    remarks: Optional[str]
    report_pdf_url: Optional[str]
    audited_by: Optional[int]
    audited_at: Optional[datetime]
    audit_status: Optional[str]
    audit_comments: Optional[str]
    fraud_flags: List[FraudFlagOut] = []


class TatStat(BaseModel):
    total: int
    on_time: int
    breached: int
    avg_hours: float
    breach_pct: float

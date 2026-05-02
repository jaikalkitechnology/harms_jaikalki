"""Phase 4.5 super-admin schemas."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── System Config ─────────────────────────────────────────────────────
class SystemConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: Any = None
    category: str
    description: Optional[str] = None
    is_secret: bool
    updated_at: Optional[datetime] = None


class SystemConfigUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: Any = None
    category: str = "general"
    description: Optional[str] = None
    is_secret: bool = False


# ── Permission CRUD ───────────────────────────────────────────────────
class PermissionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    description: Optional[str] = None
    category: str = Field(min_length=1, max_length=64)


class PermissionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None


# ── Role CRUD ─────────────────────────────────────────────────────────
class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=80)
    level: int = Field(ge=0, le=100)
    description: Optional[str] = None
    permission_codes: List[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = Field(default=None, ge=0, le=100)
    description: Optional[str] = None


class RoleWithPermissions(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    level: int
    description: Optional[str] = None
    permission_codes: List[str] = Field(default_factory=list)


class RolePermissionAssign(BaseModel):
    permission_codes: List[str] = Field(default_factory=list)


# ── Admin user management ─────────────────────────────────────────────
class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    is_admin_portal: bool
    mfa_enabled: bool
    role_codes: List[str] = Field(default_factory=list)
    last_login_at: Optional[datetime] = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=128)
    phone: Optional[str] = None
    password: str = Field(min_length=8, max_length=128)
    role_codes: List[str] = Field(default_factory=list, min_length=1)


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role_codes: Optional[List[str]] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


# ── Module settings ───────────────────────────────────────────────────
class ModuleSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_code: str
    name: str
    description: Optional[str] = None
    is_enabled: bool
    is_core: bool
    config: Any = None


class ModuleSettingUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    config: Any = None


# ── Audit logs ────────────────────────────────────────────────────────
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: Optional[int] = None
    actor_label: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    request_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    payload: Any = None
    occurred_at: datetime


# ── Branding ──────────────────────────────────────────────────────────
class BrandingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    font_family: str
    login_background_url: Optional[str] = None
    custom_domain: Optional[str] = None
    extras: Any = None


class BrandingUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    login_background_url: Optional[str] = None
    custom_domain: Optional[str] = None
    extras: Any = None


# ── Backups ───────────────────────────────────────────────────────────
class DatabaseBackupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    size_bytes: int
    status: str
    error: Optional[str] = None
    triggered_by: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# ── API keys ──────────────────────────────────────────────────────────
class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_prefix: str
    scopes: Optional[list] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    rate_limit_per_minute: Optional[int] = None
    created_at: Optional[datetime] = None


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, le=100000)


class ApiKeyCreated(ApiKeyOut):
    """Includes the plain text key — returned ONLY on creation."""

    plain_key: str


# ── Email templates ───────────────────────────────────────────────────
class EmailTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables: Optional[list] = None
    is_active: bool
    updated_at: Optional[datetime] = None


class EmailTemplateUpsert(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=160)
    subject: str = Field(min_length=2, max_length=255)
    body_html: str = Field(min_length=2)
    body_text: Optional[str] = None
    variables: List[str] = Field(default_factory=list)
    is_active: bool = True


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateTestRequest(BaseModel):
    to_email: EmailStr
    sample_variables: dict[str, Any] = Field(default_factory=dict)

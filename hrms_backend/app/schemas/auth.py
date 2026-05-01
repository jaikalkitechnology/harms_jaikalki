from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    is_admin_portal: bool
    mfa_enabled: bool
    last_login_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
    remember_me: bool = False


class AdminLoginRequest(LoginRequest):
    mfa_code: Optional[str] = Field(default=None, min_length=6, max_length=6)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    user: UserOut
    role: Optional[str] = None
    role_level: int = 0
    roles: List[str] = []
    permissions: List[str] = []


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=4, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=128)


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: Optional[str] = None
    category: str


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    level: int
    description: Optional[str] = None

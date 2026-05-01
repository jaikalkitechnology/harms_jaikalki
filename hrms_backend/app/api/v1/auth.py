from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError
from app.core.permissions import primary_role
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UserOut,
)
from app.services.auth_service import (
    authenticate_user,
    change_password as change_password_service,
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    user = await authenticate_user(db, body.email, body.password)
    refresh_days = (
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS if body.remember_me else 7
    )
    access, refresh, expires_in = await issue_token_pair(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        refresh_days=refresh_days,
    )
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    _, access, refresh_tok, expires_in = await rotate_refresh_token(
        db,
        body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    return TokenPair(
        access_token=access, refresh_token=refresh_tok, expires_in=expires_in
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    await revoke_refresh_token(db, body.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    role_codes = user.role_codes
    return MeResponse(
        user=UserOut.model_validate(user),
        role=primary_role(role_codes),
        role_level=user.max_role_level,
        roles=role_codes,
        permissions=user.permission_codes,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    await change_password_service(db, user, body.old_password, body.new_password)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Generate + email a 6-digit OTP. Always returns 202 to prevent
    email enumeration."""
    from app.services import password_reset_service

    ip = request.client.host if request.client else None
    await password_reset_service.request_otp(db, email=body.email, ip=ip)
    return {"detail": "If the account exists, an OTP has been sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    from app.services import password_reset_service

    await password_reset_service.reset(
        db,
        email=body.email,
        otp=body.otp,
        new_password=body.new_password,
    )


# ─── MFA (TOTP) ──────────────────────────────────────────────────────
class _MfaEnrollResponse(BaseModel):  # noqa: N801 — local response model
    secret: str
    otpauth_uri: str


class _MfaCodeBody(BaseModel):  # noqa: N801
    code: str


class _MfaEnableResponse(BaseModel):  # noqa: N801
    backup_codes: list[str]


@router.post("/mfa/enroll", response_model=_MfaEnrollResponse)
async def mfa_enroll(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> _MfaEnrollResponse:
    from app.services import mfa_service

    secret, uri = await mfa_service.begin_enrollment(db, user)
    return _MfaEnrollResponse(secret=secret, otpauth_uri=uri)


@router.post("/mfa/verify", response_model=_MfaEnableResponse)
async def mfa_verify(
    body: _MfaCodeBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> _MfaEnableResponse:
    from app.services import mfa_service

    codes = await mfa_service.complete_enrollment(db, user, code=body.code)
    return _MfaEnableResponse(backup_codes=codes)


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_disable(
    body: _MfaCodeBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    from app.services import mfa_service

    await mfa_service.disable(db, user, code=body.code)

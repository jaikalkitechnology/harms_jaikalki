from fastapi import APIRouter, Depends, Request, status
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
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    # Phase 1 stub: real OTP delivery (SMS/email) ships in Phase 5.
    # We return 202 regardless to avoid email enumeration.
    return {"detail": "If the account exists, an OTP has been sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    # Phase 1 stub — proper OTP store + verification arrives in Phase 5.
    raise NotFoundError("OTP flow not yet enabled")

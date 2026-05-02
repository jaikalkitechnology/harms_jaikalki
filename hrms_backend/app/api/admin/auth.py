from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.permissions import Role as RoleEnum
from app.core.permissions import primary_role
from app.core.security import generate_csrf_token
from app.dependencies import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    REFRESH_COOKIE,
    get_current_admin_user,
    get_db,
)
from app.models import User
from app.schemas.auth import AdminLoginRequest, MeResponse, UserOut
from app.services.auth_service import (
    authenticate_user,
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["admin-auth"])

ADMIN_ACCESS_MIN = 60 * 8  # 8 hours
ADMIN_REFRESH_DAYS = 1


def _set_admin_cookies(
    response: Response, access: str, refresh: str
) -> str:
    csrf = generate_csrf_token()
    secure = settings.ENVIRONMENT == "production"
    common = {
        "secure": secure,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=ADMIN_ACCESS_MIN * 60,
        httponly=True,
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=ADMIN_REFRESH_DAYS * 86_400,
        httponly=True,
        **common,
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        max_age=ADMIN_ACCESS_MIN * 60,
        httponly=False,  # JS reads this and echoes it back in X-CSRF-Token
        **common,
    )
    return csrf


def _clear_admin_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/")


@router.post("/login", response_model=MeResponse)
async def admin_login(
    body: AdminLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    user = await authenticate_user(db, body.email, body.password)
    if not user.is_admin_portal:
        raise UnauthorizedError("This account cannot access the admin portal")

    # Force MFA for super-admin (Phase 1.5 task).
    if RoleEnum.SUPER_ADMIN.value in user.role_codes and user.mfa_enabled:
        if not body.mfa_code:
            raise UnauthorizedError("MFA code required")
        if not _verify_mfa_code(user, body.mfa_code):
            raise UnauthorizedError("Invalid MFA code")

    access, refresh, _ = await issue_token_pair(
        db,
        user,
        access_minutes=ADMIN_ACCESS_MIN,
        refresh_days=ADMIN_REFRESH_DAYS,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    _set_admin_cookies(response, access, refresh)

    return _me(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def admin_logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    _: User = Depends(get_current_admin_user),
) -> None:
    if refresh_cookie:
        await revoke_refresh_token(db, refresh_cookie)
    _clear_admin_cookies(response)


@router.post("/refresh", response_model=MeResponse)
async def admin_refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> MeResponse:
    if not refresh_cookie:
        raise UnauthorizedError("No refresh cookie")
    user, access, refresh, _ = await rotate_refresh_token(
        db,
        refresh_cookie,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    _set_admin_cookies(response, access, refresh)
    return _me(user)


@router.get("/me", response_model=MeResponse)
async def admin_me(user: User = Depends(get_current_admin_user)) -> MeResponse:
    return _me(user)


def _me(user: User) -> MeResponse:
    role_codes = user.role_codes
    return MeResponse(
        user=UserOut.model_validate(user),
        role=primary_role(role_codes),
        role_level=user.max_role_level,
        roles=role_codes,
        permissions=user.permission_codes,
    )


def _verify_mfa_code(user: User, code: str) -> bool:
    """Phase 1.5 placeholder MFA check.

    For development, accept the canonical static code "000000" so the React
    admin's 2FA prompt can be exercised without real TOTP setup. The real
    implementation (pyotp) lands alongside the Super Admin module in Phase 4.5.
    """
    _ = user
    if datetime.now(timezone.utc).year < 2027 and code == "000000":
        return True
    return False

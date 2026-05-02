from typing import AsyncGenerator, Optional

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.models import User
from app.services.auth_service import get_user_by_id


ACCESS_COOKIE = "jaikalki_access"
REFRESH_COOKIE = "jaikalki_refresh"
CSRF_COOKIE = "jaikalki_csrf"
CSRF_HEADER = "x-csrf-token"


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def _extract_token(
    authorization: Optional[str], cookie_token: Optional[str]
) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return cookie_token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
    access_cookie: Optional[str] = Cookie(default=None, alias=ACCESS_COOKIE),
) -> User:
    token = _extract_token(authorization, access_cookie)
    if not token:
        raise UnauthorizedError("Not authenticated")
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc))
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    user = await get_user_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found")
    request.state.user = user
    return user


async def get_current_admin_user(
    request: Request,
    user: User = Depends(get_current_user),
    csrf_cookie: Optional[str] = Cookie(default=None, alias=CSRF_COOKIE),
    csrf_header: Optional[str] = Header(default=None, alias=CSRF_HEADER),
) -> User:
    from app.core.permissions import can_access_admin_portal

    if not can_access_admin_portal(user.role_codes, user.is_admin_portal):
        raise UnauthorizedError("Admin portal access required")
    # CSRF check is enforced for non-GET requests.
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            raise UnauthorizedError("CSRF token missing or invalid")
    return user

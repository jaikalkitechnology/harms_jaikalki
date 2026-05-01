from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, User


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    user = (
        await db.execute(select(User).where(User.email == email.lower()))
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return user


async def issue_token_pair(
    db: AsyncSession,
    user: User,
    *,
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
    access_minutes: Optional[int] = None,
    refresh_days: Optional[int] = None,
) -> tuple[str, str, int]:
    access = create_access_token(
        user.id,
        extra={"email": user.email},
        expires_minutes=access_minutes,
    )
    refresh, jti, exp = create_refresh_token(user.id, expires_days=refresh_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=exp.replace(tzinfo=None),
            user_agent=(user_agent or "")[:255] or None,
            ip=(ip or "")[:64] or None,
        )
    )
    await db.commit()
    return access, refresh, _seconds_until(exp)


async def rotate_refresh_token(
    db: AsyncSession,
    refresh_token: str,
    *,
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
) -> tuple[User, str, str, int]:
    payload = _decode_refresh(refresh_token)
    jti = payload["jti"]
    user_id = int(payload["sub"])

    record = (
        await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    ).scalar_one_or_none()
    if not record or record.revoked or record.user_id != user_id:
        raise UnauthorizedError("Refresh token revoked")

    record.revoked = True
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    access, new_refresh, expires_in = await issue_token_pair(
        db, user, user_agent=user_agent, ip=ip
    )
    return user, access, new_refresh, expires_in


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> None:
    try:
        payload = _decode_refresh(refresh_token)
    except ValueError:
        return
    jti = payload.get("jti")
    if not jti:
        return
    record = (
        await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    ).scalar_one_or_none()
    if record and not record.revoked:
        record.revoked = True
        await db.commit()


async def revoke_all_for_user(db: AsyncSession, user_id: int) -> None:
    rows = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
            )
        )
    ).scalars().all()
    for r in rows:
        r.revoked = True
    await db.commit()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    return (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()


async def change_password(
    db: AsyncSession, user: User, old_password: str, new_password: str
) -> None:
    if not verify_password(old_password, user.password_hash):
        raise UnauthorizedError("Old password is incorrect")
    user.password_hash = hash_password(new_password)
    await db.commit()
    await revoke_all_for_user(db, user.id)


def _decode_refresh(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Not a refresh token")
    return payload


def _seconds_until(when: datetime) -> int:
    now = datetime.now(timezone.utc)
    target = when if when.tzinfo else when.replace(tzinfo=timezone.utc)
    return max(0, int((target - now).total_seconds()))

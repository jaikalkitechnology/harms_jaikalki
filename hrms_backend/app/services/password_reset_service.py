"""Password reset OTP flow."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models import PasswordResetOtp, User
from app.services.email_service import send_template_email


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def request_otp(
    db: AsyncSession, *, email: str, ip: Optional[str] = None
) -> bool:
    """Always returns True so callers can't enumerate users.

    The OTP is only generated + emailed if the email actually maps to a
    real user. Existing un-consumed OTPs for the same email are
    invalidated.
    """
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if not user or not user.is_active:
        return True

    # Invalidate older un-consumed OTPs for this email.
    rows = (
        await db.execute(
            select(PasswordResetOtp)
            .where(PasswordResetOtp.email == email)
            .where(PasswordResetOtp.consumed_at.is_(None))
        )
    ).scalars().all()
    for r in rows:
        r.consumed_at = _now()

    raw = f"{secrets.randbelow(10**6):06d}"
    db.add(
        PasswordResetOtp(
            email=email,
            otp_hash=hash_password(raw),
            expires_at=_now()
            + timedelta(minutes=settings.PASSWORD_RESET_OTP_TTL_MINUTES),
            ip=ip,
        )
    )
    await db.commit()

    await send_template_email(
        to_email=user.email,
        to_name=user.full_name,
        template="password_reset_otp",
        params={
            "name": user.full_name or user.email,
            "otp": raw,
            "ttl": str(settings.PASSWORD_RESET_OTP_TTL_MINUTES),
        },
    )
    return True


async def reset(
    db: AsyncSession,
    *,
    email: str,
    otp: str,
    new_password: str,
) -> User:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if not user:
        raise NotFoundError("Account not found")

    candidate = (
        await db.execute(
            select(PasswordResetOtp)
            .where(PasswordResetOtp.email == email)
            .where(PasswordResetOtp.consumed_at.is_(None))
            .order_by(PasswordResetOtp.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not candidate:
        raise ValidationError("No active reset code — request a new one")
    if candidate.expires_at < _now():
        raise ValidationError("Code expired — request a new one")
    candidate.attempts += 1
    if candidate.attempts > settings.PASSWORD_RESET_MAX_ATTEMPTS:
        candidate.consumed_at = _now()
        await db.commit()
        raise ForbiddenError(
            "Too many attempts — request a new code"
        )
    if not verify_password(otp, candidate.otp_hash):
        await db.commit()
        raise ValidationError("Incorrect code")

    if len(new_password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    user.password_hash = hash_password(new_password)
    candidate.consumed_at = _now()
    await db.commit()
    await db.refresh(user)
    return user

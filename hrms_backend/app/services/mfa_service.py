"""MFA TOTP enrollment + verification using pyotp."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, ValidationError
from app.core.security import hash_password, verify_password
from app.models import MfaBackupCode, User


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_required_for(user: User) -> bool:
    return bool(set(user.role_codes) & set(settings.MFA_REQUIRED_ROLES))


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(*, secret: str, account_name: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name=settings.MFA_ISSUER
    )


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


# ─── DB-bound helpers ───────────────────────────────────────────────
async def begin_enrollment(
    db: AsyncSession, user: User
) -> tuple[str, str]:
    """Generate a fresh secret and store it on the user (not yet enabled).

    Returns (secret, otpauth_uri) so the client can render a QR code.
    """
    if user.mfa_enabled:
        raise ConflictError("MFA is already enabled for this account")
    secret = generate_secret()
    user.mfa_secret = secret
    await db.commit()
    await db.refresh(user)
    uri = provisioning_uri(secret=secret, account_name=user.email)
    return secret, uri


async def complete_enrollment(
    db: AsyncSession, user: User, *, code: str
) -> list[str]:
    """Verify the first TOTP, flip mfa_enabled=True, return backup codes."""
    if user.mfa_enabled:
        raise ConflictError("MFA is already enabled")
    if not user.mfa_secret:
        raise ValidationError("Call /mfa/enroll first to generate a secret")
    if not verify_totp(user.mfa_secret, code):
        raise ValidationError("Invalid verification code")
    user.mfa_enabled = True
    # Issue 8 single-use backup codes (raw codes returned, hashes stored).
    raw_codes: list[str] = []
    for _ in range(8):
        code_raw = secrets.token_hex(4).upper()  # 8-char hex
        formatted = f"{code_raw[:4]}-{code_raw[4:]}"
        raw_codes.append(formatted)
        db.add(
            MfaBackupCode(
                user_id=user.id,
                code_hash=hash_password(formatted),
            )
        )
    await db.commit()
    await db.refresh(user)
    return raw_codes


async def disable(
    db: AsyncSession, user: User, *, code: str
) -> None:
    """Require a valid TOTP / backup code before disabling MFA."""
    if not user.mfa_enabled:
        raise ConflictError("MFA is not enabled")
    if not _verify_code_or_backup(user, code, db_for_backup=None):
        raise ForbiddenError("Invalid MFA code")
    # Also consume backup if used
    if not verify_totp(user.mfa_secret, code):
        await _consume_backup(db, user, code)
    user.mfa_enabled = False
    user.mfa_secret = None
    # Wipe backup codes
    backups = (
        await db.execute(
            select(MfaBackupCode).where(MfaBackupCode.user_id == user.id)
        )
    ).scalars().all()
    for b in backups:
        await db.delete(b)
    await db.commit()
    await db.refresh(user)


def _verify_code_or_backup(
    user: User, code: str, *, db_for_backup
) -> bool:
    """Sync part: TOTP only (backup checked separately because it needs DB)."""
    return verify_totp(user.mfa_secret or "", code)


async def verify_for_login(
    db: AsyncSession, user: User, *, code: str
) -> bool:
    """Returns True if `code` is a valid TOTP or unused backup code."""
    if not user.mfa_enabled:
        return True
    if verify_totp(user.mfa_secret or "", code):
        return True
    return await _consume_backup(db, user, code)


async def _consume_backup(
    db: AsyncSession, user: User, code: str
) -> bool:
    backups = (
        await db.execute(
            select(MfaBackupCode)
            .where(MfaBackupCode.user_id == user.id)
            .where(MfaBackupCode.used_at.is_(None))
        )
    ).scalars().all()
    for b in backups:
        if verify_password(code, b.code_hash):
            b.used_at = _now()
            await db.commit()
            return True
    return False

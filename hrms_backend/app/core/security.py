import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGO = settings.JWT_ALGORITHM


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str | int,
    *,
    extra: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    expire = _now() + timedelta(
        minutes=expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": _now(),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGO)


def create_refresh_token(
    subject: str | int,
    *,
    expires_days: int | None = None,
    persistent: bool = False,
) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at). Caller persists the jti for revocation.

    ``persistent`` marks a "keep me signed in" session; rotation keeps
    renewing it for JWT_PERSISTENT_REFRESH_DAYS."""
    jti = secrets.token_urlsafe(32)
    expire = _now() + timedelta(
        days=expires_days or settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": _now(),
        "jti": jti,
        "type": "refresh",
    }
    if persistent:
        payload["persistent"] = True
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGO)
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGO])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

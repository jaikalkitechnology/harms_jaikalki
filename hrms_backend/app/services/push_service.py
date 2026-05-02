"""Firebase Cloud Messaging (FCM) push sender.

Initialised lazily on first call so the FastAPI process boots cleanly even
without a Firebase service account configured (dev/test). When
`FCM_CREDENTIALS_PATH` is unset, `send_push()` returns `(False, "fcm
disabled")` and the caller falls back to in-app + email.

In production set:

    FCM_CREDENTIALS_PATH=/run/secrets/firebase-service-account.json
    FCM_PROJECT_ID=jaikalki-hrms

The service-account JSON is the file Firebase Console gives you under
Project Settings → Service accounts → "Generate new private key".
"""
from __future__ import annotations

import logging
from threading import Lock
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_lock = Lock()
_app = None
_messaging = None


def _ensure_initialised() -> bool:
    global _app, _messaging
    if _messaging is not None:
        return True
    if not settings.FCM_CREDENTIALS_PATH:
        return False
    with _lock:
        if _messaging is not None:
            return True
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            if not firebase_admin._apps:  # type: ignore[attr-defined]
                cred = credentials.Certificate(settings.FCM_CREDENTIALS_PATH)
                _app = firebase_admin.initialize_app(
                    cred,
                    options=(
                        {"projectId": settings.FCM_PROJECT_ID}
                        if settings.FCM_PROJECT_ID
                        else None
                    ),
                )
            _messaging = messaging
            return True
        except Exception:
            logger.exception("Firebase Admin init failed")
            return False


def send_push(
    *,
    token: str,
    title: str,
    body: Optional[str],
    data: Optional[dict] = None,
) -> tuple[bool, Optional[str]]:
    """Returns (ok, error). Falls back to a no-op when FCM isn't configured."""
    if not _ensure_initialised():
        return False, "fcm disabled"
    try:
        import firebase_admin  # noqa: F401  # ensure init has run

        message = _messaging.Message(  # type: ignore[union-attr]
            notification=_messaging.Notification(  # type: ignore[union-attr]
                title=title, body=body or ""
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        msg_id = _messaging.send(message)  # type: ignore[union-attr]
        logger.info("FCM sent: %s", msg_id)
        return True, None
    except Exception as exc:
        logger.exception("FCM send failed")
        return False, f"{exc.__class__.__name__}: {exc}"


def send_push_multicast(
    *,
    tokens: list[str],
    title: str,
    body: Optional[str],
    data: Optional[dict] = None,
) -> tuple[int, int]:
    """Returns (success_count, failure_count). Empty token list is a no-op."""
    if not tokens or not _ensure_initialised():
        return 0, len(tokens)
    try:
        message = _messaging.MulticastMessage(  # type: ignore[union-attr]
            notification=_messaging.Notification(  # type: ignore[union-attr]
                title=title, body=body or ""
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )
        resp = _messaging.send_each_for_multicast(message)  # type: ignore[union-attr]
        return resp.success_count, resp.failure_count
    except Exception:
        logger.exception("FCM multicast failed")
        return 0, len(tokens)

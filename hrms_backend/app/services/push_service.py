"""Firebase Cloud Messaging (FCM) push sender.

Initialised lazily on first call so the FastAPI process boots cleanly even
without a Firebase service account configured (dev/test). Two ways to
configure:

1. Explicit path:  FCM_CREDENTIALS_PATH=/path/to/service-account.json
2. Auto-discovery: drop the JSON in `app/credential/` — the first file
   matching `*firebase*adminsdk*.json` is picked up automatically.

In production we also recommend setting FCM_PROJECT_ID so messages
are unambiguously routed.

The service-account JSON is the file Firebase Console gives you under
Project Settings → Service accounts → "Generate new private key".
"""
from __future__ import annotations

import glob
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_lock = Lock()
_app = None
_messaging = None


def _resolve_credentials_path() -> Optional[str]:
    """Return the configured path, or auto-discover one in app/credential/."""
    if settings.FCM_CREDENTIALS_PATH:
        if os.path.isfile(settings.FCM_CREDENTIALS_PATH):
            return settings.FCM_CREDENTIALS_PATH
        logger.warning(
            "FCM_CREDENTIALS_PATH=%s does not exist; falling back to auto-discovery",
            settings.FCM_CREDENTIALS_PATH,
        )

    # Auto-discover: app/credential/*firebase*adminsdk*.json
    cred_dir = Path(__file__).resolve().parents[1] / "credential"
    if cred_dir.is_dir():
        candidates = sorted(glob.glob(str(cred_dir / "*firebase*adminsdk*.json")))
        if not candidates:
            candidates = sorted(glob.glob(str(cred_dir / "*.json")))
        if candidates:
            return candidates[0]
    return None


def _ensure_initialised() -> bool:
    global _app, _messaging
    if _messaging is not None:
        return True
    cred_path = _resolve_credentials_path()
    if not cred_path:
        return False
    with _lock:
        if _messaging is not None:
            return True
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            if not firebase_admin._apps:  # type: ignore[attr-defined]
                cred = credentials.Certificate(cred_path)
                _app = firebase_admin.initialize_app(
                    cred,
                    options=(
                        {"projectId": settings.FCM_PROJECT_ID}
                        if settings.FCM_PROJECT_ID
                        else None
                    ),
                )
            _messaging = messaging
            logger.info(
                "FCM initialised: project=%s credentials=%s",
                settings.FCM_PROJECT_ID or "(default)",
                cred_path,
            )
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


def status() -> dict:
    """Diagnostic helper for /health/ready and ops dashboards."""
    cred_path = _resolve_credentials_path()
    return {
        "configured": cred_path is not None,
        "credentials_path": cred_path,
        "project_id": settings.FCM_PROJECT_ID,
        "initialised": _messaging is not None,
    }


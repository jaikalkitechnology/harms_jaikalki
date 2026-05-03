import io

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config import settings
from app.dependencies import get_db
from app.schemas.health import HealthCheck, ReadinessCheck
from app.services.cache import ping_redis
from app.services.push_service import status as push_status
from app.services.storage import delete, storage_info, upload_fileobj

router = APIRouter()


def _safe_redis_url() -> str:
    """Return REDIS_URL with the password (if any) masked, so we can
    show it in health responses without leaking secrets."""
    raw = settings.REDIS_URL or ""
    # redis://[user[:password]@]host[:port][/db]
    if "@" in raw and "://" in raw:
        scheme, rest = raw.split("://", 1)
        creds, host = rest.split("@", 1)
        if ":" in creds:
            user, _ = creds.split(":", 1)
            return f"{scheme}://{user}:***@{host}"
        return f"{scheme}://***@{host}"
    return raw


@router.get("/health", response_model=HealthCheck)
async def health(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment dependent
        db_status = f"error: {exc.__class__.__name__}"

    redis_status = "ok"
    try:
        await ping_redis()
    except Exception as exc:  # pragma: no cover - environment dependent
        # Surface the actual error string + (sanitised) configured URL so
        # the operator can see immediately whether it's a refused
        # connection, an auth failure, the wrong host, etc.
        redis_status = f"error: {exc.__class__.__name__}: {str(exc)[:160]} | url={_safe_redis_url()}"

    return HealthCheck(
        status="ok",
        app=settings.APP_NAME,
        version=__version__,
        environment=settings.ENVIRONMENT,
        company=settings.COMPANY_NAME,
        db=db_status,
        redis=redis_status,
    )


@router.get("/health/live", summary="Liveness probe — process is up")
async def health_live() -> dict:
    return {"status": "ok", "version": __version__}


@router.get(
    "/health/ready",
    response_model=ReadinessCheck,
    summary="Readiness probe — DB, Redis, storage all reachable",
)
async def health_ready(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> ReadinessCheck:
    checks: dict = {}

    # Database round-trip
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = {"status": "ok"}
    except Exception as exc:
        checks["db"] = {"status": "down", "error": exc.__class__.__name__}

    # Redis round-trip (degraded, not fatal — caching is best-effort)
    try:
        await ping_redis()
        checks["redis"] = {"status": "ok", "url": _safe_redis_url()}
    except Exception as exc:
        checks["redis"] = {
            "status": "down",
            "error": exc.__class__.__name__,
            "detail": str(exc)[:200],
            "url": _safe_redis_url(),
        }

    # Storage write + delete round-trip
    storage_check: dict = {"info": storage_info()}
    try:
        key, _ = upload_fileobj(
            io.BytesIO(b"healthcheck"),
            key_prefix="_healthcheck",
            filename="probe.txt",
            content_type="text/plain",
        )
        delete(key)
        storage_check["status"] = "ok"
    except Exception as exc:
        storage_check["status"] = "down"
        storage_check["error"] = exc.__class__.__name__
    checks["storage"] = storage_check

    # FCM — informational only. Push is optional; the API stays "ok" even
    # when FCM isn't configured (notifications fall back to in-app + email).
    fcm = push_status()
    checks["fcm"] = {
        **fcm,
        "status": "ok" if fcm["configured"] else "disabled",
    }

    # Aggregate status: db + storage are required; redis is degraded-only.
    critical = (checks["db"]["status"], checks["storage"]["status"])
    if any(s == "down" for s in critical):
        overall = "down"
        response.status_code = 503
    elif checks["redis"]["status"] != "ok":
        overall = "degraded"
    else:
        overall = "ok"

    return ReadinessCheck(status=overall, checks=checks)

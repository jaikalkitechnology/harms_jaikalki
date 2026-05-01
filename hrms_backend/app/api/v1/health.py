from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config import settings
from app.dependencies import get_db
from app.schemas.health import HealthCheck
from app.services.cache import ping_redis

router = APIRouter()


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
        redis_status = f"error: {exc.__class__.__name__}"

    return HealthCheck(
        status="ok",
        app=settings.APP_NAME,
        version=__version__,
        environment=settings.ENVIRONMENT,
        company=settings.COMPANY_NAME,
        db=db_status,
        redis=redis_status,
    )

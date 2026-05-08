import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__

# ─── Sentry — initialise BEFORE the FastAPI app so middleware is wrapped ──
def _init_sentry() -> None:
    from app.config import settings as _s

    if not _s.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=_s.SENTRY_DSN,
            environment=_s.SENTRY_ENVIRONMENT or _s.ENVIRONMENT,
            release=f"hrms@{__version__}",
            traces_sample_rate=_s.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
        )
    except Exception:
        logging.getLogger(__name__).warning(
            "Sentry init failed; continuing without error reporting."
        )


_init_sentry()
from app.api.router import admin_router, v1_router
from app.api.v1.health import router as health_router
from app.config import settings
from app.core.exceptions import AppException
from app.core.middleware import (
    AuditMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from app.database import init_tables
from app.services.cache import close_redis, get_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional dev convenience — only runs when explicitly enabled.
    # Production environments should run `alembic upgrade head` instead.
    if settings.AUTO_CREATE_TABLES:
        try:
            await init_tables()
            logger.info("AUTO_CREATE_TABLES: schema synced with models")
        except Exception:
            logger.exception("init_tables failed; continuing startup")
        try:
            from app.database import sync_columns
            await sync_columns()
            logger.info("AUTO_CREATE_TABLES: column sync complete")
        except Exception:
            logger.exception("sync_columns failed; continuing startup")
        try:
            from app.database import AsyncSessionLocal
            from app.core.permissions import ROLE_PERMISSIONS
            from app.models import Permission, Role, RolePermission
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                roles = {
                    r.code: r
                    for r in (
                        await db.execute(select(Role))
                    ).scalars().all()
                }
                perms = {
                    p.code: p
                    for p in (
                        await db.execute(select(Permission))
                    ).scalars().all()
                }
                existing_pairs = {
                    (rp.role_id, rp.permission_id)
                    for rp in (
                        await db.execute(select(RolePermission))
                    ).scalars().all()
                }
                added = 0
                for role_code, perm_codes in ROLE_PERMISSIONS.items():
                    role = roles.get(role_code)
                    if not role:
                        continue
                    for pcode in perm_codes:
                        perm = perms.get(pcode)
                        if not perm:
                            continue
                        if (role.id, perm.id) in existing_pairs:
                            continue
                        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
                        existing_pairs.add((role.id, perm.id))
                        added += 1
                if added:
                    await db.commit()
                    logger.info("role-permission sync added %s rows", added)
        except Exception:
            logger.exception(
                "role-permission sync failed; continuing startup"
            )

    get_redis()
    yield
    await close_redis()


from app.utils.ist_response import ISTJSONResponse

app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description=f"{settings.COMPANY_NAME} — Human Resource Management System API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    # Convert every datetime in JSON responses to Asia/Kolkata at the
    # wire — backend stores naive UTC, callers see IST with +05:30.
    default_response_class=ISTJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-ms"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=20, window_seconds=60)
app.add_middleware(AuditMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Local-storage backend: expose the uploads directory at the configured URL
# prefix so files written by `app.services.storage.upload_fileobj` are
# downloadable. Only mounted when STORAGE_BACKEND is "local".
if (settings.STORAGE_BACKEND or "local").lower() == "local":
    os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
    app.mount(
        "/" + settings.LOCAL_STORAGE_URL_PREFIX.strip("/"),
        StaticFiles(directory=settings.LOCAL_STORAGE_PATH),
        name="uploads",
    )


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "detail": exc.detail},
    )


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "app": settings.APP_NAME,
        "company": settings.COMPANY_NAME,
        "version": __version__,
        "docs": "/docs",
    }


app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_ADMIN_PREFIX)
app.include_router(health_router, tags=["health"])

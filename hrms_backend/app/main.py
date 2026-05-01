from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.router import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.core.middleware import RequestIDMiddleware
from app.services.cache import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm Redis connection on startup
    get_redis()
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description=f"{settings.COMPANY_NAME} — Human Resource Management System API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")


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


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Also expose /health at the root for simple uptime checks.
from app.api.v1.health import router as health_router  # noqa: E402

app.include_router(health_router, tags=["health"])

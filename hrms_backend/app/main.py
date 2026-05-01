from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.router import admin_router, v1_router
from app.api.v1.health import router as health_router
from app.config import settings
from app.core.exceptions import AppException
from app.core.middleware import RequestIDMiddleware
from app.services.cache import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    expose_headers=["X-Request-ID", "X-Response-Time-ms"],
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


app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_ADMIN_PREFIX)
app.include_router(health_router, tags=["health"])

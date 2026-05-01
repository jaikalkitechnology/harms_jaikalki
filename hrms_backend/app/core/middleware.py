import time
import uuid
from collections import deque
from threading import Lock

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.2f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP-aligned response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(self), camera=(self), microphone=(), payment=()",
        )
        # Only assert HSTS in production (avoids dev-server lockouts).
        if (settings.ENVIRONMENT or "").lower() == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window rate limiter for sensitive endpoints.

    Defaults: 20 requests per 60 seconds, keyed by client IP, applied only
    to high-risk paths (auth + admin login + Justice submission). For
    multi-instance deployments, swap this for a Redis-backed limiter.
    """

    SENSITIVE_PREFIXES = (
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/admin/auth",
        "/api/v1/justice/submit",
    )

    def __init__(
        self,
        app,
        *,
        max_requests: int = 20,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = {}
        self._lock = Lock()

    def _is_sensitive(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.SENSITIVE_PREFIXES)

    def _client_ip(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._is_sensitive(request.url.path):
            return await call_next(request)

        now = time.monotonic()
        key = f"{self._client_ip(request)}:{request.url.path}"
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": "rate_limit_exceeded",
                        "detail": (
                            f"Too many requests. Try again in {retry_after}s."
                        ),
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)
        return await call_next(request)

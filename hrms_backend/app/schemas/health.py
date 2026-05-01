from typing import Any, Dict

from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    company: str
    db: str
    redis: str


class ReadinessCheck(BaseModel):
    """Deep readiness probe — used by load balancers + CI smoke tests."""

    status: str  # "ok" | "degraded" | "down"
    checks: Dict[str, Any]

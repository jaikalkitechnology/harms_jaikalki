from fastapi import APIRouter

from app.api.v1.health import router as v1_health_router

api_router = APIRouter()
api_router.include_router(v1_health_router, tags=["health"])

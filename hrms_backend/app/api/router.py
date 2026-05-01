from fastapi import APIRouter

from app.api.admin.auth import router as admin_auth_router
from app.api.admin.permissions import router as admin_permissions_router
from app.api.v1.auth import router as v1_auth_router
from app.api.v1.health import router as v1_health_router

# Mounted at /api/v1
v1_router = APIRouter()
v1_router.include_router(v1_health_router, tags=["health"])
v1_router.include_router(v1_auth_router)

# Mounted at /api/admin
admin_router = APIRouter()
admin_router.include_router(admin_auth_router)
admin_router.include_router(admin_permissions_router)

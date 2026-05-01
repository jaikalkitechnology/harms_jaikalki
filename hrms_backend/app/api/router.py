from fastapi import APIRouter

from app.api.admin.auth import router as admin_auth_router
from app.api.admin.permissions import router as admin_permissions_router
from app.api.v1.approvals import router as v1_approvals_router
from app.api.v1.attendance import router as v1_attendance_router
from app.api.v1.auth import router as v1_auth_router
from app.api.v1.dashboard import router as v1_dashboard_router
from app.api.v1.documents import router as v1_documents_router
from app.api.v1.employees import router as v1_employees_router
from app.api.v1.health import router as v1_health_router
from app.api.v1.intern_expenses import router as v1_intern_expenses_router
from app.api.v1.leaves import router as v1_leaves_router
from app.api.v1.organization import router as v1_organization_router
from app.api.v1.salary_templates import router as v1_salary_templates_router

# Mounted at /api/v1
v1_router = APIRouter()
v1_router.include_router(v1_health_router, tags=["health"])
v1_router.include_router(v1_auth_router)
v1_router.include_router(v1_dashboard_router)
v1_router.include_router(v1_employees_router)
v1_router.include_router(v1_organization_router)
v1_router.include_router(v1_salary_templates_router)
v1_router.include_router(v1_intern_expenses_router)
v1_router.include_router(v1_documents_router)
v1_router.include_router(v1_attendance_router)
v1_router.include_router(v1_leaves_router)
v1_router.include_router(v1_approvals_router)

# Mounted at /api/admin
admin_router = APIRouter()
admin_router.include_router(admin_auth_router)
admin_router.include_router(admin_permissions_router)

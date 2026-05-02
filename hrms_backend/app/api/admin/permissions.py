"""Read-only helpers for the current admin's effective permissions.

Full CRUD on permissions/roles lives in app.api.admin.super_admin (Phase 4.5)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_admin_user, get_db
from app.models import User

router = APIRouter(tags=["admin-permissions"])


@router.get("/me/permissions", response_model=list[str])
async def my_permissions(
    user: User = Depends(get_current_admin_user),
) -> list[str]:
    return user.permission_codes


@router.get("/users/{user_id}/permissions", response_model=list[str])
async def user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.view")),
) -> list[str]:
    target = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not target:
        raise NotFoundError("User not found")
    return target.permission_codes

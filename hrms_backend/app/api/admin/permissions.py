from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission, require_super_admin
from app.dependencies import get_current_admin_user, get_db
from app.models import Permission, Role, User
from app.schemas.auth import PermissionOut, RoleOut

router = APIRouter(prefix="/admin", tags=["admin-permissions"])


@router.get("/permissions", response_model=list[PermissionOut])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
) -> list[PermissionOut]:
    rows = (await db.execute(select(Permission).order_by(Permission.code))).scalars().all()
    return [PermissionOut.model_validate(r) for r in rows]


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.roles.view")),
) -> list[RoleOut]:
    rows = (await db.execute(select(Role).order_by(Role.level.desc()))).scalars().all()
    return [RoleOut.model_validate(r) for r in rows]


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

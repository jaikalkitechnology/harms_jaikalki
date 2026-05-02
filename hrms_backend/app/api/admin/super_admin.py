"""Phase 4.5 — Super Admin endpoints.

All routes require the super-admin role. Mounted under /api/admin so the
final paths are /api/admin/system/..., /api/admin/permissions/...,
/api/admin/roles/..., /api/admin/admins/..., /api/admin/modules/...,
/api/admin/audit-logs/..., /api/admin/branding, /api/admin/backups/...,
/api/admin/api-keys/..., /api/admin/email-templates/...
"""
from __future__ import annotations

import os
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import require_super_admin
from app.core.security import hash_password
from app.dependencies import get_db
from app.models import (
    ApiKey,
    AuditLog,
    BrandingSettings,
    DatabaseBackup,
    EmailTemplate,
    ModuleSetting,
    Permission,
    Role,
    RolePermission,
    SystemConfig,
    User,
    UserRole,
)
from app.schemas.auth import PermissionOut
from app.schemas.super_admin import (
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyOut,
    AuditLogOut,
    BrandingOut,
    BrandingUpdate,
    DatabaseBackupOut,
    EmailTemplateOut,
    EmailTemplateTestRequest,
    EmailTemplateUpdate,
    EmailTemplateUpsert,
    ModuleSettingOut,
    ModuleSettingUpdate,
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RolePermissionAssign,
    RoleUpdate,
    RoleWithPermissions,
    SystemConfigOut,
    SystemConfigUpsert,
)
from app.services.audit_service import log as audit_log

router = APIRouter(tags=["super-admin"])


# Helper: log an admin action against AuditLog using the actor user.
async def _record(
    db: AsyncSession,
    request: Request,
    actor: User,
    action: str,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[str | int] = None,
    payload: Optional[dict] = None,
) -> None:
    await audit_log(
        db,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        method=request.method,
        path=str(request.url.path),
        payload=payload,
    )


# ── System config ─────────────────────────────────────────────────────
@router.get("/system/config", response_model=list[SystemConfigOut])
async def list_system_config(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    stmt = select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
    if category:
        stmt = stmt.where(SystemConfig.category == category)
    rows = (await db.execute(stmt)).scalars().all()
    return [SystemConfigOut.model_validate(r) for r in rows]


@router.put("/system/config", response_model=SystemConfigOut)
async def upsert_system_config(
    body: SystemConfigUpsert,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    existing = (
        await db.execute(select(SystemConfig).where(SystemConfig.key == body.key))
    ).scalar_one_or_none()
    if existing:
        existing.value = body.value
        existing.category = body.category
        existing.description = body.description
        existing.is_secret = body.is_secret
        existing.updated_by = actor.id
        row = existing
    else:
        row = SystemConfig(
            key=body.key,
            value=body.value,
            category=body.category,
            description=body.description,
            is_secret=body.is_secret,
            updated_by=actor.id,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "system.config.upsert",
                  entity_type="system_config", entity_id=row.id,
                  payload={"key": body.key, "category": body.category})
    return SystemConfigOut.model_validate(row)


@router.get("/system/health")
async def system_health(_: User = Depends(require_super_admin())):
    return {
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "now": datetime.utcnow().isoformat(),
    }


# ── Permissions CRUD ──────────────────────────────────────────────────
@router.get("/permissions", response_model=list[PermissionOut])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(select(Permission).order_by(Permission.category, Permission.code))
    ).scalars().all()
    return [PermissionOut.model_validate(r) for r in rows]


@router.get("/permissions/categories", response_model=list[str])
async def list_permission_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (await db.execute(select(Permission.category).distinct())).scalars().all()
    return sorted(c for c in rows if c)


@router.post("/permissions", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
async def create_permission(
    body: PermissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    existing = (
        await db.execute(select(Permission).where(Permission.code == body.code))
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("Permission with this code already exists")
    row = Permission(code=body.code, description=body.description, category=body.category)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "permission.create",
                  entity_type="permission", entity_id=row.id, payload=body.model_dump())
    return PermissionOut.model_validate(row)


@router.put("/permissions/{perm_id}", response_model=PermissionOut)
async def update_permission(
    perm_id: int,
    body: PermissionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (
        await db.execute(select(Permission).where(Permission.id == perm_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundError("Permission not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "permission.update",
                  entity_type="permission", entity_id=perm_id, payload=data)
    return PermissionOut.model_validate(row)


@router.delete("/permissions/{perm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    perm_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (
        await db.execute(select(Permission).where(Permission.id == perm_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundError("Permission not found")
    # Cascade-delete role grants.
    await db.execute(
        RolePermission.__table__.delete().where(
            RolePermission.permission_id == perm_id
        )
    )
    await db.delete(row)
    await db.commit()
    await _record(db, request, actor, "permission.delete",
                  entity_type="permission", entity_id=perm_id)


# ── Roles CRUD ────────────────────────────────────────────────────────
async def _role_with_permissions(db: AsyncSession, role: Role) -> RoleWithPermissions:
    perms = (
        await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
    ).scalars().all()
    data = RoleWithPermissions.model_validate(role).model_copy(
        update={"permission_codes": sorted(perms)}
    )
    return data


@router.get("/roles", response_model=list[RoleWithPermissions])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    roles = (await db.execute(select(Role).order_by(Role.level.desc()))).scalars().all()
    return [await _role_with_permissions(db, r) for r in roles]


@router.post("/roles", response_model=RoleWithPermissions, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    if (await db.execute(select(Role).where(Role.code == body.code))).scalar_one_or_none():
        raise ConflictError("Role code already exists")
    role = Role(code=body.code, name=body.name, level=body.level, description=body.description)
    db.add(role)
    await db.flush()
    if body.permission_codes:
        perms = (
            await db.execute(
                select(Permission).where(Permission.code.in_(body.permission_codes))
            )
        ).scalars().all()
        for p in perms:
            db.add(RolePermission(role_id=role.id, permission_id=p.id))
    await db.commit()
    await db.refresh(role)
    await _record(db, request, actor, "role.create",
                  entity_type="role", entity_id=role.id,
                  payload={"code": body.code, "permissions": body.permission_codes})
    return await _role_with_permissions(db, role)


@router.put("/roles/{role_id}", response_model=RoleWithPermissions)
async def update_role(
    role_id: int,
    body: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    role = (await db.execute(select(Role).where(Role.id == role_id))).scalar_one_or_none()
    if not role:
        raise NotFoundError("Role not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(role, k, v)
    await db.commit()
    await db.refresh(role)
    await _record(db, request, actor, "role.update",
                  entity_type="role", entity_id=role_id, payload=data)
    return await _role_with_permissions(db, role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    role = (await db.execute(select(Role).where(Role.id == role_id))).scalar_one_or_none()
    if not role:
        raise NotFoundError("Role not found")
    if role.code == "super_admin":
        raise ValidationError("Cannot delete the super_admin role")
    await db.execute(
        RolePermission.__table__.delete().where(RolePermission.role_id == role_id)
    )
    await db.execute(UserRole.__table__.delete().where(UserRole.role_id == role_id))
    await db.delete(role)
    await db.commit()
    await _record(db, request, actor, "role.delete",
                  entity_type="role", entity_id=role_id)


@router.post("/roles/{role_id}/permissions", response_model=RoleWithPermissions)
async def assign_role_permissions(
    role_id: int,
    body: RolePermissionAssign,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    role = (await db.execute(select(Role).where(Role.id == role_id))).scalar_one_or_none()
    if not role:
        raise NotFoundError("Role not found")
    # Replace the full permission set on this role.
    await db.execute(
        RolePermission.__table__.delete().where(RolePermission.role_id == role_id)
    )
    if body.permission_codes:
        perms = (
            await db.execute(
                select(Permission).where(Permission.code.in_(body.permission_codes))
            )
        ).scalars().all()
        for p in perms:
            db.add(RolePermission(role_id=role.id, permission_id=p.id))
    await db.commit()
    await db.refresh(role)
    await _record(db, request, actor, "role.permissions.assign",
                  entity_type="role", entity_id=role_id,
                  payload={"permission_codes": body.permission_codes})
    return await _role_with_permissions(db, role)


@router.get("/roles/{role_id}/users", response_model=list[int])
async def list_role_users(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(select(UserRole.user_id).where(UserRole.role_id == role_id))
    ).scalars().all()
    return list(rows)


# ── Admin user management ─────────────────────────────────────────────
async def _user_role_codes(db: AsyncSession, user_id: int) -> list[str]:
    rows = (
        await db.execute(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
    ).scalars().all()
    return sorted(rows)


def _admin_out(user: User, role_codes: list[str]) -> AdminUserOut:
    return AdminUserOut.model_validate(user).model_copy(
        update={"role_codes": role_codes}
    )


@router.get("/admins", response_model=list[AdminUserOut])
async def list_admins(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(
            select(User).where(User.is_admin_portal == True).order_by(User.email)  # noqa: E712
        )
    ).scalars().all()
    out: list[AdminUserOut] = []
    for u in rows:
        codes = await _user_role_codes(db, u.id)
        out.append(_admin_out(u, codes))
    return out


@router.post("/admins", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_admin(
    body: AdminUserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    existing = (
        await db.execute(select(User).where(User.email == body.email.lower()))
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("User with this email already exists")
    user = User(
        email=body.email.lower(),
        full_name=body.full_name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        is_active=True,
        is_admin_portal=True,
    )
    db.add(user)
    await db.flush()
    if body.role_codes:
        roles = (
            await db.execute(select(Role).where(Role.code.in_(body.role_codes)))
        ).scalars().all()
        for r in roles:
            db.add(UserRole(user_id=user.id, role_id=r.id))
    await db.commit()
    await db.refresh(user)
    await _record(db, request, actor, "admin.create",
                  entity_type="user", entity_id=user.id,
                  payload={"email": user.email, "roles": body.role_codes})
    codes = await _user_role_codes(db, user.id)
    return _admin_out(user, codes)


@router.put("/admins/{user_id}", response_model=AdminUserOut)
async def update_admin(
    user_id: int,
    body: AdminUserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise NotFoundError("Admin not found")
    data = body.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data.pop("password"))
    elif "password" in data:
        data.pop("password")
    role_codes = data.pop("role_codes", None)
    for k, v in data.items():
        setattr(user, k, v)
    if role_codes is not None:
        await db.execute(
            UserRole.__table__.delete().where(UserRole.user_id == user_id)
        )
        if role_codes:
            roles = (
                await db.execute(select(Role).where(Role.code.in_(role_codes)))
            ).scalars().all()
            for r in roles:
                db.add(UserRole(user_id=user.id, role_id=r.id))
    await db.commit()
    await db.refresh(user)
    await _record(db, request, actor, "admin.update",
                  entity_type="user", entity_id=user_id,
                  payload={k: v for k, v in body.model_dump(exclude_unset=True).items() if k != "password"})
    codes = await _user_role_codes(db, user.id)
    return _admin_out(user, codes)


@router.delete("/admins/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise NotFoundError("Admin not found")
    if actor.id == user.id:
        raise ValidationError("Cannot remove your own admin access")
    user.is_active = False
    user.is_admin_portal = False
    await db.commit()
    await _record(db, request, actor, "admin.deactivate",
                  entity_type="user", entity_id=user_id)


@router.post("/admins/{user_id}/permissions", response_model=AdminUserOut)
async def set_admin_role_assignment(
    user_id: int,
    body: RolePermissionAssign,  # we reuse this — `permission_codes` here = role codes
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    """Replace this admin's role assignments. The body uses
    `permission_codes` to carry role codes — keeping a single shape for
    the React form."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise NotFoundError("Admin not found")
    await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))
    if body.permission_codes:
        roles = (
            await db.execute(select(Role).where(Role.code.in_(body.permission_codes)))
        ).scalars().all()
        for r in roles:
            db.add(UserRole(user_id=user.id, role_id=r.id))
    await db.commit()
    await _record(db, request, actor, "admin.roles.assign",
                  entity_type="user", entity_id=user_id,
                  payload={"role_codes": body.permission_codes})
    codes = await _user_role_codes(db, user.id)
    return _admin_out(user, codes)


@router.get("/admins/{user_id}/audit", response_model=list[AuditLogOut])
async def admin_audit_trail(
    user_id: int,
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(
            select(AuditLog)
            .where(AuditLog.actor_user_id == user_id)
            .order_by(AuditLog.occurred_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [AuditLogOut.model_validate(r) for r in rows]


# ── Modules ───────────────────────────────────────────────────────────
DEFAULT_MODULES = [
    ("attendance", "Attendance & Leave", True),
    ("payroll", "Payroll", True),
    ("dwp", "Daily Work Planning", True),
    ("justice", "Justice Portal", True),
    ("field_force", "Field Force", True),
    ("lms", "LMS & Examinations", False),
    ("trainer", "Trainer Module", False),
    ("performance", "Performance Management", False),
    ("polish", "Workplace Polish (Assets, Visitors, Jobs)", False),
]


async def _ensure_default_modules(db: AsyncSession) -> None:
    existing = {
        m.module_code
        for m in (await db.execute(select(ModuleSetting))).scalars().all()
    }
    added = False
    for code, name, is_core in DEFAULT_MODULES:
        if code in existing:
            continue
        db.add(
            ModuleSetting(
                module_code=code, name=name, is_core=is_core, is_enabled=True
            )
        )
        added = True
    if added:
        await db.commit()


@router.get("/modules", response_model=list[ModuleSettingOut])
async def list_modules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    await _ensure_default_modules(db)
    rows = (await db.execute(select(ModuleSetting).order_by(ModuleSetting.module_code))).scalars().all()
    return [ModuleSettingOut.model_validate(r) for r in rows]


@router.put("/modules/{module_id}", response_model=ModuleSettingOut)
async def update_module(
    module_id: int,
    body: ModuleSettingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (
        await db.execute(select(ModuleSetting).where(ModuleSetting.id == module_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundError("Module not found")
    if row.is_core and body.is_enabled is False:
        raise ValidationError("Cannot disable a core module")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by = actor.id
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "module.update",
                  entity_type="module", entity_id=module_id, payload=data)
    return ModuleSettingOut.model_validate(row)


# ── Audit logs ────────────────────────────────────────────────────────
@router.get("/audit-logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    actor_user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    since_days: Optional[int] = Query(default=None, ge=1, le=365),
    limit: int = Query(default=200, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    from app.services.audit_service import list_logs
    rows = await list_logs(
        db,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        since_days=since_days,
        limit=limit,
    )
    return [AuditLogOut.model_validate(r) for r in rows]


# ── Branding ──────────────────────────────────────────────────────────
async def _get_or_create_branding(db: AsyncSession) -> BrandingSettings:
    row = (await db.execute(select(BrandingSettings).limit(1))).scalar_one_or_none()
    if row:
        return row
    row = BrandingSettings(company_name=settings.COMPANY_NAME)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/branding", response_model=BrandingOut)
async def get_branding(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    return BrandingOut.model_validate(await _get_or_create_branding(db))


@router.put("/branding", response_model=BrandingOut)
async def update_branding(
    body: BrandingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = await _get_or_create_branding(db)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by = actor.id
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "branding.update",
                  entity_type="branding", entity_id=row.id, payload=data)
    return BrandingOut.model_validate(row)


# ── Database backups ──────────────────────────────────────────────────
@router.get("/backups", response_model=list[DatabaseBackupOut])
async def list_backups(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(
            select(DatabaseBackup).order_by(DatabaseBackup.started_at.desc()).limit(100)
        )
    ).scalars().all()
    return [DatabaseBackupOut.model_validate(r) for r in rows]


@router.post("/backups", response_model=DatabaseBackupOut, status_code=status.HTTP_201_CREATED)
async def trigger_backup(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    """Trigger an on-demand mysqldump.

    The actual dump is delegated to scripts/ops/backup.sh if present;
    otherwise we record a pending entry and let the operator pick it up.
    Designed to be safe in dev (no script → no shell-out)."""
    backup_dir = Path(os.environ.get("HRMS_BACKUP_DIR", "/var/backups/jaikalki"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"hrms_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
    file_path = backup_dir / file_name

    row = DatabaseBackup(
        file_name=file_name,
        file_path=str(file_path),
        size_bytes=0,
        status="running",
        triggered_by=actor.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    script = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "backup.sh"
    try:
        if script.is_file() and os.access(script, os.X_OK):
            subprocess.run([str(script), str(file_path)], check=True, timeout=600)
            row.size_bytes = file_path.stat().st_size if file_path.exists() else 0
            row.status = "completed"
        else:
            row.status = "pending"
            row.error = (
                "scripts/ops/backup.sh not found or not executable; "
                "operator must complete manually."
            )
        row.completed_at = datetime.utcnow()
    except Exception as e:  # noqa: BLE001
        row.status = "failed"
        row.error = str(e)[:1000]
        row.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "backup.trigger",
                  entity_type="backup", entity_id=row.id, payload={"file": file_name})
    return DatabaseBackupOut.model_validate(row)


# ── API keys ──────────────────────────────────────────────────────────
@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
    ).scalars().all()
    return [ApiKeyOut.model_validate(r) for r in rows]


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    plain = "jkt_" + secrets.token_urlsafe(32)
    key_hash = hash_password(plain)
    row = ApiKey(
        name=body.name,
        key_hash=key_hash,
        key_prefix=plain[:8],
        scopes=body.scopes,
        expires_at=body.expires_at,
        rate_limit_per_minute=body.rate_limit_per_minute,
        created_by=actor.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "api_key.create",
                  entity_type="api_key", entity_id=row.id,
                  payload={"name": row.name, "scopes": row.scopes})
    base = ApiKeyOut.model_validate(row).model_dump()
    return ApiKeyCreated(**base, plain_key=plain)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (await db.execute(select(ApiKey).where(ApiKey.id == key_id))).scalar_one_or_none()
    if not row:
        raise NotFoundError("API key not found")
    row.is_active = False
    await db.commit()
    await _record(db, request, actor, "api_key.revoke",
                  entity_type="api_key", entity_id=key_id)


# ── Email templates ───────────────────────────────────────────────────
@router.get("/email-templates", response_model=list[EmailTemplateOut])
async def list_email_templates(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin()),
):
    rows = (
        await db.execute(select(EmailTemplate).order_by(EmailTemplate.code))
    ).scalars().all()
    return [EmailTemplateOut.model_validate(r) for r in rows]


@router.post("/email-templates", response_model=EmailTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    body: EmailTemplateUpsert,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    if (
        await db.execute(select(EmailTemplate).where(EmailTemplate.code == body.code))
    ).scalar_one_or_none():
        raise ConflictError("Template code already exists")
    row = EmailTemplate(**body.model_dump(), updated_by=actor.id)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "email_template.create",
                  entity_type="email_template", entity_id=row.id,
                  payload={"code": body.code})
    return EmailTemplateOut.model_validate(row)


@router.put("/email-templates/{template_id}", response_model=EmailTemplateOut)
async def update_email_template(
    template_id: int,
    body: EmailTemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (
        await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundError("Template not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by = actor.id
    await db.commit()
    await db.refresh(row)
    await _record(db, request, actor, "email_template.update",
                  entity_type="email_template", entity_id=template_id, payload=data)
    return EmailTemplateOut.model_validate(row)


@router.delete("/email-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_template(
    template_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (
        await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundError("Template not found")
    await db.delete(row)
    await db.commit()
    await _record(db, request, actor, "email_template.delete",
                  entity_type="email_template", entity_id=template_id)


@router.post("/email-templates/{template_id}/test", status_code=status.HTTP_202_ACCEPTED)
async def send_test_email(
    template_id: int,
    body: EmailTemplateTestRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_super_admin()),
):
    row = (
        await db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
    ).scalar_one_or_none()
    if not row:
        raise NotFoundError("Template not found")
    # Render with sample variables
    subject = row.subject
    body_html = row.body_html
    for k, v in body.sample_variables.items():
        token = "{{" + k + "}}"
        subject = subject.replace(token, str(v))
        body_html = body_html.replace(token, str(v))
    try:
        from app.services.email_service import send_email
        ok, err = await send_email(
            to_email=body.to_email,
            to_name=None,
            subject=subject,
            html=body_html,
        )
        sent = ok
        error: Optional[str] = err
    except Exception as e:  # noqa: BLE001
        sent = False
        error = str(e)
    await _record(db, request, actor, "email_template.test",
                  entity_type="email_template", entity_id=template_id,
                  payload={"to": body.to_email, "sent": sent, "error": error})
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Failed to send",
        )
    return {"sent": True}

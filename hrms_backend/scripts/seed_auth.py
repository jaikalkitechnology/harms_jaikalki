"""Seed roles, permissions, and default users.

Run with:

    python -m scripts.seed_auth

Idempotent — safe to run multiple times.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import (
    PERMISSIONS,
    ROLE_LEVELS,
    ROLE_PERMISSIONS,
    Role as RoleEnum,
)
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import (
    Department,
    Designation,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)


ROLE_DEFS: list[dict[str, str | int]] = [
    {
        "code": RoleEnum.SUPER_ADMIN.value,
        "name": "Super Admin",
        "description": "Full system access, can edit everything",
    },
    {
        "code": RoleEnum.DIRECTOR.value,
        "name": "Director",
        "description": "Top-level executive; sees everything read-only by default",
    },
    {
        "code": RoleEnum.HR.value,
        "name": "HR",
        "description": "Human Resources team",
    },
    {
        "code": RoleEnum.ADMIN.value,
        "name": "Admin",
        "description": "Operational admin / configurable",
    },
    {
        "code": RoleEnum.MANAGER.value,
        "name": "Manager",
        "description": "Team manager",
    },
    {
        "code": RoleEnum.EMPLOYEE.value,
        "name": "Employee",
        "description": "Permanent / Trainee / Contract employee",
    },
    {
        "code": RoleEnum.TRAINER.value,
        "name": "Trainer",
        "description": "LMS trainer",
    },
    {
        "code": RoleEnum.FIELD.value,
        "name": "Field Force",
        "description": "Field-force employee",
    },
    {
        "code": RoleEnum.INTERN.value,
        "name": "Intern",
        "description": "Travel-expense only intern",
    },
]


DEPARTMENTS = [
    ("Engineering", "ENG"),
    ("Human Resources", "HR"),
    ("Operations", "OPS"),
    ("Sales", "SAL"),
]


# (email, full_name, password, [role_codes], is_admin_portal, designation_name)
DEFAULT_USERS = [
    (
        "super@jaikalki.com",
        "Super Admin",
        "super123",
        [RoleEnum.SUPER_ADMIN.value],
        True,
        "Super Admin",
    ),
    (
        "admin@hrms.com",
        "Director Demo",
        "admin123",
        [RoleEnum.DIRECTOR.value],
        True,
        "Director",
    ),
    (
        "hr@hrms.com",
        "HR Demo",
        "hr123",
        [RoleEnum.HR.value],
        True,
        "HR Manager",
    ),
    (
        "admin2@hrms.com",
        "Admin Demo",
        "admin123",
        [RoleEnum.ADMIN.value],
        True,
        "Admin",
    ),
    (
        "manager@hrms.com",
        "Manager Demo",
        "manager123",
        [RoleEnum.MANAGER.value],
        False,
        "Engineering Manager",
    ),
    (
        "employee@hrms.com",
        "Employee Demo",
        "employee123",
        [RoleEnum.EMPLOYEE.value],
        False,
        "Software Engineer",
    ),
]


async def seed_permissions(db: AsyncSession) -> dict[str, Permission]:
    existing = {
        p.code: p
        for p in (await db.execute(select(Permission))).scalars().all()
    }
    for code, desc, category in PERMISSIONS:
        if code not in existing:
            obj = Permission(code=code, description=desc, category=category)
            db.add(obj)
            existing[code] = obj
    await db.flush()
    return existing


async def seed_roles(
    db: AsyncSession, perms: dict[str, Permission]
) -> dict[str, Role]:
    existing = {
        r.code: r for r in (await db.execute(select(Role))).scalars().all()
    }
    for spec in ROLE_DEFS:
        code = spec["code"]
        role = existing.get(code)
        if not role:
            role = Role(
                code=code,
                name=spec["name"],
                description=spec.get("description"),
                level=ROLE_LEVELS.get(code, 1),
            )
            db.add(role)
            existing[code] = role
        else:
            role.level = ROLE_LEVELS.get(code, role.level)
    await db.flush()

    # Attach permissions per role.
    existing_pairs = {
        (rp.role_id, rp.permission_id)
        for rp in (await db.execute(select(RolePermission))).scalars().all()
    }
    for role_code, perm_codes in ROLE_PERMISSIONS.items():
        role = existing.get(role_code)
        if not role:
            continue
        for code in perm_codes:
            perm = perms.get(code)
            if not perm:
                continue
            if (role.id, perm.id) in existing_pairs:
                continue
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
            existing_pairs.add((role.id, perm.id))
    await db.flush()
    return existing


async def seed_departments(db: AsyncSession) -> dict[str, Department]:
    existing = {
        d.code: d for d in (await db.execute(select(Department))).scalars().all()
    }
    for name, code in DEPARTMENTS:
        if code not in existing:
            d = Department(name=name, code=code)
            db.add(d)
            existing[code] = d
    await db.flush()
    return existing


async def seed_users(db: AsyncSession, roles: dict[str, Role]) -> None:
    existing = {
        u.email: u for u in (await db.execute(select(User))).scalars().all()
    }
    for email, full_name, pw, role_codes, is_admin, _designation in DEFAULT_USERS:
        user = existing.get(email)
        if not user:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(pw),
                is_active=True,
                is_admin_portal=is_admin,
            )
            db.add(user)
            await db.flush()
            existing[email] = user
        else:
            user.is_admin_portal = is_admin

        current = {ur.role_id for ur in user.roles}
        for code in role_codes:
            role = roles.get(code)
            if role and role.id not in current:
                db.add(UserRole(user_id=user.id, role_id=role.id))
                current.add(role.id)
    await db.flush()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        perms = await seed_permissions(db)
        roles = await seed_roles(db, perms)
        await seed_departments(db)
        await seed_users(db, roles)
        await db.commit()
    print("✔ Seed complete")
    print("  Login candidates:")
    for email, _, pw, *_rest in DEFAULT_USERS:
        print(f"   - {email}  /  {pw}")
    print("  MFA dev code (super-admin if mfa_enabled=true): 000000")


if __name__ == "__main__":
    asyncio.run(run())

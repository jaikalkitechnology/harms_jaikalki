"""RBAC role + permission registry, decorators, and FastAPI dependencies."""
from enum import Enum
from functools import wraps
from typing import Callable, Iterable

from fastapi import Depends

from app.core.exceptions import ForbiddenError


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    DIRECTOR = "director"
    HR = "hr"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    FIELD = "field"
    TRAINER = "trainer"
    INTERN = "intern"


# Role level hierarchy (higher = more privilege).
ROLE_LEVELS: dict[str, int] = {
    Role.SUPER_ADMIN.value: 6,
    Role.DIRECTOR.value: 5,
    Role.HR.value: 4,
    Role.ADMIN.value: 3,
    Role.MANAGER.value: 3,
    Role.TRAINER.value: 2,
    Role.FIELD.value: 2,
    Role.EMPLOYEE.value: 1,
    Role.INTERN.value: 1,
}


# Permission registry — keep this list curated; the seeder uses it.
PERMISSIONS: list[tuple[str, str, str]] = [
    # employee
    ("employee.view.self", "View own employee profile", "employee"),
    ("employee.view.team", "View team employee profiles", "employee"),
    ("employee.view.all", "View all employees", "employee"),
    ("employee.create", "Create new employees", "employee"),
    ("employee.update", "Update employee data", "employee"),
    ("employee.delete", "Delete employees", "employee"),
    # attendance
    ("attendance.mark.self", "Mark own attendance", "attendance"),
    ("attendance.view.team", "View team attendance", "attendance"),
    ("attendance.view.all", "View all attendance", "attendance"),
    # leave
    ("leave.apply", "Apply for leave", "leave"),
    ("leave.approve.team", "Approve team leave", "leave"),
    ("leave.approve.all", "Approve any leave", "leave"),
    # salary / payroll
    ("salary.view.self", "View own salary", "payroll"),
    ("salary.view.team", "View team salaries", "payroll"),
    ("salary.view.all", "View all salaries", "payroll"),
    ("payroll.run", "Run payroll", "payroll"),
    ("payroll.export", "Export payroll", "payroll"),
    # approvals
    ("approval.view.team", "View team approvals", "approval"),
    ("approval.view.all", "View all approvals", "approval"),
    ("approval.act", "Act on approvals", "approval"),
    # reports
    ("report.view.team", "View team reports", "report"),
    ("report.view.all", "View all reports", "report"),
    # admin
    ("admin.users.view", "View admin user list", "admin"),
    ("admin.users.manage", "Manage admin users", "admin"),
    ("admin.roles.view", "View roles", "admin"),
    ("admin.roles.manage", "Manage roles & permissions", "admin"),
    ("admin.audit.view", "View audit logs", "admin"),
    # super-admin
    ("system.config", "Edit system config", "system"),
    ("system.modules", "Toggle modules", "system"),
    ("system.branding", "Edit branding", "system"),
]

PERMISSION_CODES: list[str] = [code for code, _, _ in PERMISSIONS]


# Default role → permission grants used by the seeder.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    Role.SUPER_ADMIN.value: PERMISSION_CODES,  # everything
    Role.DIRECTOR.value: [
        "employee.view.all",
        "employee.update",
        "salary.view.all",
        "salary.view.team",
        "attendance.view.all",
        "payroll.run",
        "payroll.export",
        "approval.view.all",
        "approval.act",
        "report.view.all",
        "leave.approve.all",
        "leave.approve.team",
    ],
    Role.HR.value: [
        "employee.view.all",
        "employee.create",
        "employee.update",
        "salary.view.all",
        "salary.view.team",
        "attendance.view.all",
        "payroll.run",
        "payroll.export",
        "approval.view.all",
        "approval.act",
        "leave.approve.all",
        "leave.approve.team",
        "report.view.all",
        "admin.users.view",
    ],
    Role.ADMIN.value: [
        "employee.view.all",
        "employee.create",
        "employee.update",
        "salary.view.all",
        "salary.view.team",
        "attendance.view.all",
        "approval.view.all",
        "approval.act",
        "leave.approve.all",
        "leave.approve.team",
        "payroll.run",
        "payroll.export",
        "report.view.all",
        "admin.users.view",
        "admin.users.manage",
        "admin.roles.view",
        "admin.audit.view",
    ],
    Role.MANAGER.value: [
        "employee.view.team",
        "salary.view.team",
        "attendance.view.team",
        "leave.approve.team",
        "approval.view.team",
        "approval.act",
        "report.view.team",
    ],
    Role.EMPLOYEE.value: [
        "employee.view.self",
        "salary.view.self",
        "attendance.mark.self",
        "leave.apply",
    ],
    Role.TRAINER.value: [
        "employee.view.self",
        "attendance.mark.self",
        "leave.apply",
    ],
    Role.FIELD.value: [
        "employee.view.self",
        "salary.view.self",
        "attendance.mark.self",
        "leave.apply",
    ],
    Role.INTERN.value: [
        "employee.view.self",
        "attendance.mark.self",
        "leave.apply",
    ],
}


def primary_role(role_codes: Iterable[str]) -> str | None:
    """Return the highest-privilege role from a set of role codes."""
    best: str | None = None
    best_level = -1
    for code in role_codes:
        level = ROLE_LEVELS.get(code, 0)
        if level > best_level:
            best, best_level = code, level
    return best


# ── FastAPI dependencies / decorators ────────────────────────────────────

def require_permission(permission: str) -> Callable:
    from app.dependencies import get_current_user

    def _checker(user=Depends(get_current_user)):
        if permission not in user.permission_codes and "system.config" not in user.permission_codes:
            # super-admin shortcut: anyone with system.config bypasses
            raise ForbiddenError(f"Missing permission: {permission}")
        return user

    return _checker


def require_role(*roles: str) -> Callable:
    from app.dependencies import get_current_user

    def _checker(user=Depends(get_current_user)):
        if not set(user.role_codes) & set(roles):
            raise ForbiddenError(
                f"Requires one of roles: {', '.join(roles)}"
            )
        return user

    return _checker


def require_level(min_level: int) -> Callable:
    from app.dependencies import get_current_user

    def _checker(user=Depends(get_current_user)):
        if user.max_role_level < min_level:
            raise ForbiddenError(f"Requires role level ≥ {min_level}")
        return user

    return _checker


def require_super_admin() -> Callable:
    return require_role(Role.SUPER_ADMIN.value)


# Roles allowed to sign into the admin web portal. The per-user
# `users.is_admin_portal` flag remains a manual override for accounts
# whose role isn't on this list but should still get in.
ADMIN_PORTAL_ROLES: set[str] = {
    Role.SUPER_ADMIN.value,
    Role.DIRECTOR.value,
    Role.HR.value,
    Role.ADMIN.value,
}


def can_access_admin_portal(role_codes: Iterable[str], is_admin_portal: bool) -> bool:
    if is_admin_portal:
        return True
    return bool(set(role_codes) & ADMIN_PORTAL_ROLES)

"""Role/permission scaffolding. Filled in by Phase 1 (Auth & RBAC)."""
from enum import Enum


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DIRECTOR = "director"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    FIELD = "field"
    TRAINER = "trainer"
    INTERN = "intern"

"""Employee CRUD + scoping + Jaikalki-specific workflows."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, Optional, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import Role as RoleEnum
from app.core.security import hash_password
from app.models import (
    EmergencyContact,
    Employee,
    EmployeeAddress,
    EmployeeBankDetails,
    EmployeeCategory,
    EmployeeProbation,
    FamilyMember,
    Role,
    SalaryTemplate,
    User,
    UserRole,
)
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


# ── Visibility rules ───────────────────────────────────────────────────
def can_see_all(user: User) -> bool:
    """Director, HR, Admin, Super Admin see every employee."""
    privileged = {
        RoleEnum.SUPER_ADMIN.value,
        RoleEnum.DIRECTOR.value,
        RoleEnum.HR.value,
        RoleEnum.ADMIN.value,
    }
    return bool(set(user.role_codes) & privileged)


def is_manager(user: User) -> bool:
    return RoleEnum.MANAGER.value in user.role_codes


async def get_self_employee(db: AsyncSession, user: User) -> Optional[Employee]:
    return (
        await db.execute(select(Employee).where(Employee.user_id == user.id))
    ).scalar_one_or_none()


async def visible_employee_ids(db: AsyncSession, user: User) -> Optional[set[int]]:
    """Return the set of employee IDs the user is allowed to see.

    Returns None when the user can see everyone (no filter needed).
    """
    if can_see_all(user):
        return None

    self_emp = await get_self_employee(db, user)
    ids: set[int] = set()
    if self_emp:
        ids.add(self_emp.id)

    if is_manager(user) and self_emp:
        # Direct reportees
        rows = (
            await db.execute(
                select(Employee.id).where(Employee.reporting_to == self_emp.id)
            )
        ).scalars().all()
        ids.update(rows)

    return ids


def assert_can_view(user: User, target: Employee, allowed_ids: Optional[set[int]]) -> None:
    if allowed_ids is None:
        return
    if target.id not in allowed_ids:
        raise ForbiddenError("Not allowed to view this employee")


# ── Leave-approver visibility (manager + HR/admin + dept mapping) ───────
async def _mapped_approver_department_ids(
    db: AsyncSession, user: User
) -> set[int]:
    """Departments that have explicitly mapped this user as a leave
    approver (set in the admin panel)."""
    from app.models import Department

    rows = (
        await db.execute(
            select(Department.id, Department.leave_approver_user_ids)
        )
    ).all()
    out: set[int] = set()
    for dept_id, ids in rows:
        if ids and user.id in ids:
            out.add(dept_id)
    return out


async def is_leave_approver(db: AsyncSession, user: User) -> bool:
    """A user may act on leave approvals if their role grants
    ``leave.approve.team`` OR they are mapped as a department approver."""
    if "leave.approve.team" in user.permission_codes:
        return True
    return bool(await _mapped_approver_department_ids(db, user))


async def leave_visible_employee_ids(
    db: AsyncSession, user: User
) -> Optional[set[int]]:
    """Employee IDs whose leave this user may see/decide.

    Returns ``None`` (no filter — sees everyone) for HR/Admin/Director.
    Otherwise the union of the manager's reportees (and self) and every
    employee in a department this user is mapped to approve for.
    """
    base = await visible_employee_ids(db, user)
    if base is None:
        return None
    ids: set[int] = set(base)
    dept_ids = await _mapped_approver_department_ids(db, user)
    if dept_ids:
        rows = (
            await db.execute(
                select(Employee.id).where(Employee.department_id.in_(dept_ids))
            )
        ).scalars().all()
        ids.update(rows)
    return ids


# ── Code generation ────────────────────────────────────────────────────
async def next_employee_code(db: AsyncSession) -> str:
    prefix = settings.EMPLOYEE_CODE_PREFIX
    rows = (
        await db.execute(
            select(Employee.employee_code).where(
                Employee.employee_code.like(f"{prefix}%")
            )
        )
    ).scalars().all()
    max_n = 0
    for code in rows:
        suffix = code[len(prefix) :]
        if suffix.isdigit():
            max_n = max(max_n, int(suffix))
    return f"{prefix}{max_n + 1:03d}"


# ── Lookups ───────────────────────────────────────────────────────────
async def get_category(
    db: AsyncSession, *, code: Optional[str] = None, id: Optional[int] = None
) -> EmployeeCategory:
    if id is not None:
        cat = (
            await db.execute(select(EmployeeCategory).where(EmployeeCategory.id == id))
        ).scalar_one_or_none()
    elif code:
        cat = (
            await db.execute(
                select(EmployeeCategory).where(EmployeeCategory.code == code.upper())
            )
        ).scalar_one_or_none()
    else:
        raise ValidationError("category_code or category_id is required")
    if not cat:
        raise NotFoundError("Employee category not found")
    return cat


async def get_template(
    db: AsyncSession, template_id: Optional[int]
) -> Optional[SalaryTemplate]:
    if template_id is None:
        return None
    t = (
        await db.execute(select(SalaryTemplate).where(SalaryTemplate.id == template_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Salary template not found")
    return t


# ── Create / update ────────────────────────────────────────────────────
async def create_employee(
    db: AsyncSession, payload: EmployeeCreate, current_user: User
) -> Employee:
    category = await get_category(
        db, code=payload.category_code, id=payload.category_id
    )
    template = await get_template(db, payload.salary_template_id)

    # Sanity for interns: no salary, only travel.
    if category.only_travel_expense:
        if payload.ctc_annual and payload.ctc_annual > Decimal("0"):
            raise ValidationError("Interns cannot have a CTC; remove ctc_annual.")
        if template and template.category != "intern":
            raise ValidationError("Intern category requires an intern salary template.")

    # Generate employee code.
    code = await next_employee_code(db)

    # Optional: create a companion User account.
    user_id: Optional[int] = None
    if payload.create_user_account:
        if not payload.user_email:
            raise ValidationError("user_email is required when create_user_account is true")
        existing = (
            await db.execute(select(User).where(User.email == payload.user_email))
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("A user with that email already exists")
        user = User(
            email=payload.user_email,
            full_name=f"{payload.first_name} {payload.last_name}",
            password_hash=hash_password("changeme123"),
            is_active=True,
            is_admin_portal=False,
        )
        db.add(user)
        await db.flush()
        # Default role per category.
        role_code = {
            "INTERN": RoleEnum.INTERN.value,
            "TRAINEE": RoleEnum.EMPLOYEE.value,
            "PERMANENT": RoleEnum.EMPLOYEE.value,
            "CONTRACT": RoleEnum.EMPLOYEE.value,
        }.get(category.code, RoleEnum.EMPLOYEE.value)
        role = (
            await db.execute(select(Role).where(Role.code == role_code))
        ).scalar_one_or_none()
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.flush()
        user_id = user.id

    is_on_probation = bool(category.requires_probation)
    probation_end: Optional[date] = None
    if is_on_probation:
        months = (
            template.probation_months
            if template and template.has_probation
            else category.default_probation_months
        )
        probation_end = payload.date_of_joining + timedelta(days=30 * months)

    emp = Employee(
        user_id=user_id,
        employee_code=code,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        blood_group=payload.blood_group,
        gender=payload.gender,
        marital_status=payload.marital_status,
        personal_email=payload.personal_email,
        personal_phone=payload.personal_phone,
        category_id=category.id,
        designation_id=payload.designation_id,
        department_id=payload.department_id,
        reporting_to=payload.reporting_to,
        salary_template_id=template.id if template else None,
        ctc_annual=payload.ctc_annual or Decimal("0"),
        date_of_joining=payload.date_of_joining,
        probation_end_date=probation_end,
        work_location=payload.work_location or "Mira Road, Thane",
        employment_type=payload.employment_type or "full_time",
        work_mode=payload.work_mode or "office",
        status="active",
        is_on_probation=is_on_probation,
    )
    db.add(emp)
    await db.flush()

    if is_on_probation and probation_end:
        db.add(
            EmployeeProbation(
                employee_id=emp.id,
                probation_start_date=payload.date_of_joining,
                probation_end_date=probation_end,
                status="in_progress",
            )
        )

    await db.commit()
    await db.refresh(emp)
    return emp


async def update_employee(
    db: AsyncSession, emp: Employee, payload: EmployeeUpdate
) -> Employee:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(emp, key, value)
    await db.commit()
    await db.refresh(emp)
    return emp


async def get_employee(db: AsyncSession, employee_id: int) -> Employee:
    emp = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")
    return emp


async def list_employees(
    db: AsyncSession,
    user: User,
    *,
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    on_probation: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Employee]:
    stmt = select(Employee)

    allowed = await visible_employee_ids(db, user)
    if allowed is not None:
        if not allowed:
            return []
        stmt = stmt.where(Employee.id.in_(allowed))

    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.employee_code.ilike(like),
                Employee.personal_email.ilike(like),
            )
        )
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if category_id:
        stmt = stmt.where(Employee.category_id == category_id)
    if on_probation is not None:
        stmt = stmt.where(Employee.is_on_probation.is_(on_probation))

    stmt = stmt.order_by(Employee.employee_code).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


async def assign_manager(
    db: AsyncSession, emp: Employee, manager_id: Optional[int]
) -> Employee:
    if manager_id and manager_id == emp.id:
        raise ValidationError("An employee cannot report to themselves")
    if manager_id:
        await get_employee(db, manager_id)
    emp.reporting_to = manager_id
    await db.commit()
    await db.refresh(emp)
    return emp


# ── Probation ──────────────────────────────────────────────────────────
async def get_active_probation(
    db: AsyncSession, employee_id: int
) -> Optional[EmployeeProbation]:
    return (
        await db.execute(
            select(EmployeeProbation)
            .where(EmployeeProbation.employee_id == employee_id)
            .where(EmployeeProbation.status.in_(["in_progress", "extended"]))
            .order_by(EmployeeProbation.id.desc())
        )
    ).scalars().first()


async def confirm_employee(
    db: AsyncSession,
    emp: Employee,
    *,
    by_user: Optional[User] = None,
    confirmation_letter_url: Optional[str] = None,
    on_date: Optional[date] = None,
) -> EmployeeProbation:
    p = await get_active_probation(db, emp.id)
    if not p:
        raise ValidationError("No active probation to confirm")
    when = on_date or date.today()
    p.status = "confirmed"
    p.confirmed_date = when
    p.confirmed_by = by_user.id if by_user else None
    p.confirmation_letter_url = confirmation_letter_url

    emp.is_on_probation = False
    emp.confirmation_date = when
    # Probation effectively ends the day the employee is confirmed.
    emp.probation_end_date = when
    await db.commit()
    await db.refresh(p)
    return p


async def revert_confirmation(
    db: AsyncSession, emp: Employee
) -> Optional[EmployeeProbation]:
    """Undo a confirmation: clear the employee's confirmation_date,
    put them back on probation, and reset the probation record to its
    pre-confirmation state (restoring the originally-planned end date).
    Used when a confirmation letter is deleted."""
    p = (
        await db.execute(
            select(EmployeeProbation)
            .where(EmployeeProbation.employee_id == emp.id)
            .where(EmployeeProbation.status == "confirmed")
            .order_by(EmployeeProbation.id.desc())
        )
    ).scalars().first()

    emp.is_on_probation = True
    emp.confirmation_date = None
    if p is not None:
        # Restore the planned end (extension end wins if it was extended).
        emp.probation_end_date = p.extension_end_date or p.probation_end_date
        p.status = "extended" if p.is_extended else "in_progress"
        p.confirmed_date = None
        p.confirmed_by = None
        p.confirmation_letter_url = None
    await db.commit()
    if p is not None:
        await db.refresh(p)
    return p


async def extend_probation(
    db: AsyncSession,
    emp: Employee,
    *,
    months: int,
    reason: str,
) -> EmployeeProbation:
    p = await get_active_probation(db, emp.id)
    if not p:
        raise ValidationError("No active probation to extend")
    if p.is_extended:
        raise ValidationError("Probation has already been extended once")

    new_end = (p.extension_end_date or p.probation_end_date) + timedelta(days=30 * months)
    p.is_extended = True
    p.extension_end_date = new_end
    p.extension_reason = reason
    p.status = "extended"
    emp.probation_end_date = new_end
    await db.commit()
    await db.refresh(p)
    return p


async def expiring_probations(
    db: AsyncSession, *, days: int = 15
) -> Sequence[Employee]:
    today = date.today()
    cutoff = today + timedelta(days=days)
    rows = (
        await db.execute(
            select(Employee)
            .where(Employee.is_on_probation.is_(True))
            .where(Employee.probation_end_date.is_not(None))
            .where(Employee.probation_end_date <= cutoff)
            .where(Employee.probation_end_date >= today)
            .order_by(Employee.probation_end_date)
        )
    ).scalars().all()
    return rows


# ── Credential management ────────────────────────────────────────────
async def create_user_account_for(
    db: AsyncSession,
    *,
    employee: Employee,
    email: str,
    initial_password: str,
    role_code: Optional[str] = None,
) -> User:
    """Create a mobile-app User account linked to an existing employee.
    Idempotent on the employee side: refuses if employee already has a
    linked user."""
    if employee.user_id is not None:
        raise ConflictError("Employee already has a linked user account")
    existing = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("A user with that email already exists")
    if not initial_password or len(initial_password) < 8:
        raise ValidationError("Password must be at least 8 characters")

    user = User(
        email=email,
        full_name=f"{employee.first_name} {employee.last_name}",
        password_hash=hash_password(initial_password),
        is_active=True,
        is_admin_portal=False,
    )
    db.add(user)
    await db.flush()
    code = role_code or RoleEnum.EMPLOYEE.value
    role = (
        await db.execute(select(Role).where(Role.code == code))
    ).scalar_one_or_none()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    employee.user_id = user.id
    await db.commit()
    await db.refresh(user)
    return user


async def reset_employee_password(
    db: AsyncSession,
    *,
    employee: Employee,
    new_password: str,
) -> User:
    """Admin-initiated password reset: hashes the provided password and
    activates the account if it was disabled."""
    if employee.user_id is None:
        raise ValidationError("Employee has no linked user account")
    if not new_password or len(new_password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    user = (
        await db.execute(select(User).where(User.id == employee.user_id))
    ).scalar_one_or_none()
    if not user:
        raise NotFoundError("Linked user account not found")
    user.password_hash = hash_password(new_password)
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user


async def set_account_active(
    db: AsyncSession,
    *,
    employee: Employee,
    is_active: bool,
) -> User:
    if employee.user_id is None:
        raise ValidationError("Employee has no linked user account")
    user = (
        await db.execute(select(User).where(User.id == employee.user_id))
    ).scalar_one_or_none()
    if not user:
        raise NotFoundError("Linked user account not found")
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return user


# ── Org chart ─────────────────────────────────────────────────────────
async def org_chart(db: AsyncSession) -> list[dict]:
    """Build the full org chart as a forest of nodes."""
    rows = (await db.execute(select(Employee))).scalars().all()
    by_id: dict[int, dict] = {}
    for e in rows:
        by_id[e.id] = {
            "id": e.id,
            "employee_code": e.employee_code,
            "name": f"{e.first_name} {e.last_name}",
            "designation": e.designation.name if e.designation else None,
            "department": e.department.name if e.department else None,
            "photo_url": e.photo_url,
            "children": [],
            "_parent": e.reporting_to,
        }
    roots = []
    for node in by_id.values():
        parent_id = node.pop("_parent")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots

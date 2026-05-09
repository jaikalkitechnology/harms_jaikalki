"""Seed employee categories, salary templates, and sample employees.

Idempotent. Run after `seed_auth.py`:

    python -m scripts.seed_auth
    python -m scripts.seed_employees

Reference: hrms_structure/SALARY_STRUCTURE_JAIKALKI.md
"""
from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import (
    Department,
    Designation,
    Employee,
    EmployeeCategory,
    EmployeeProbation,
    Role,
    SalaryTemplate,
    User,
    UserRole,
)


# (code, name, eligible_pf, eligible_esic, eligible_gratuity, eligible_pl,
#  eligible_bonus, has_salary, has_stipend, only_travel_expense,
#  requires_probation, default_probation_months, description)
CATEGORIES: list[dict] = [
    dict(
        code="INTERN", name="Intern",
        eligible_for_pf=False, eligible_for_esic=False, eligible_for_gratuity=False,
        eligible_for_pl=False, eligible_for_bonus=False,
        has_salary=False, has_stipend=False, only_travel_expense=True,
        requires_probation=False, default_probation_months=0,
        description="Travel expense only — no salary",
    ),
    dict(
        code="TRAINEE", name="Trainee",
        eligible_for_pf=True, eligible_for_esic=True, eligible_for_gratuity=False,
        eligible_for_pl=False, eligible_for_bonus=False,
        has_salary=True, has_stipend=False, only_travel_expense=False,
        requires_probation=True, default_probation_months=6,
        description="With probation",
    ),
    dict(
        code="PERMANENT", name="Permanent",
        eligible_for_pf=True, eligible_for_esic=True, eligible_for_gratuity=True,
        eligible_for_pl=True, eligible_for_bonus=True,
        has_salary=True, has_stipend=False, only_travel_expense=False,
        requires_probation=True, default_probation_months=6,
        description="Confirmed employee",
    ),
    dict(
        code="CONTRACT", name="Contract",
        eligible_for_pf=True, eligible_for_esic=False, eligible_for_gratuity=False,
        eligible_for_pl=False, eligible_for_bonus=False,
        has_salary=True, has_stipend=False, only_travel_expense=False,
        requires_probation=False, default_probation_months=0,
        description="Contract employee",
    ),
]


# 8 salary templates from SALARY_STRUCTURE_JAIKALKI.md
SALARY_TEMPLATES: list[dict] = [
    dict(
        template_code="JKT-INTERN-001",
        template_name="Intern (Travel Only)",
        category="intern",
        designation_level=1,
        ctc_annual_default=Decimal("0"),
        travel_expense_max=Decimal("3000"),
        is_paid_internship=False,
        has_probation=False,
        probation_months=0,
        probation_extension_months=0,
        mediclaim_amount=Decimal("0"),
        pa_insurance_amount=Decimal("0"),
        notice_period_probation=0,
        notice_period_confirmed=0,
        notice_period_termination=7,
    ),
    # Pooja Kumawat's exact template — calculator must produce her offer letter.
    dict(
        template_code="JKT-TRAINEE-L1",
        template_name="Junior Developer (Trainee L1)",
        category="trainee",
        designation_level=1,
        ctc_annual_default=Decimal("270588"),
        basic_amount=Decimal("15000"),
        hra_amount=Decimal("4500"),
        other_allowance=Decimal("450"),
        has_probation=True,
        probation_months=6,
        probation_extension_months=2,
        mediclaim_amount=Decimal("200000"),
        pa_insurance_amount=Decimal("500000"),
        notice_period_probation=15,
        notice_period_confirmed=30,
        notice_period_termination=7,
    ),
    dict(
        template_code="JKT-PERM-L2",
        template_name="Senior Developer (L2)",
        category="permanent",
        designation_level=2,
        ctc_annual_default=Decimal("600000"),
        basic_amount=Decimal("25000"),
        hra_amount=Decimal("12500"),
        other_allowance=Decimal("7500"),
        has_probation=True,
        probation_months=6,
        probation_extension_months=2,
        mediclaim_amount=Decimal("300000"),
        pa_insurance_amount=Decimal("500000"),
    ),
    dict(
        template_code="JKT-PERM-L3",
        template_name="Tech Lead (L3)",
        category="permanent",
        designation_level=3,
        ctc_annual_default=Decimal("1200000"),
        basic_amount=Decimal("50000"),
        hra_amount=Decimal("25000"),
        other_allowance=Decimal("15000"),
        special_allowance=Decimal("5000"),
        conveyance=Decimal("1600"),
        medical_allowance=Decimal("1250"),
        has_probation=True,
        mediclaim_amount=Decimal("500000"),
        pa_insurance_amount=Decimal("1000000"),
    ),
    dict(
        template_code="JKT-PERM-L4",
        template_name="Manager (L4)",
        category="permanent",
        designation_level=4,
        ctc_annual_default=Decimal("1800000"),
        basic_amount=Decimal("75000"),
        hra_amount=Decimal("37500"),
        special_allowance=Decimal("25000"),
        lta=Decimal("5000"),
        conveyance=Decimal("1600"),
        medical_allowance=Decimal("1250"),
        food_coupon=Decimal("2200"),
        has_probation=True,
        mediclaim_amount=Decimal("750000"),
        pa_insurance_amount=Decimal("1500000"),
    ),
    dict(
        template_code="JKT-PERM-L5",
        template_name="Director / VP (L5)",
        category="permanent",
        designation_level=5,
        ctc_annual_default=Decimal("3600000"),
        basic_amount=Decimal("150000"),
        hra_amount=Decimal("75000"),
        special_allowance=Decimal("60000"),
        lta=Decimal("12500"),
        food_coupon=Decimal("2200"),
        has_probation=False,
        mediclaim_amount=Decimal("1000000"),
        pa_insurance_amount=Decimal("2500000"),
    ),
    dict(
        template_code="JKT-FIELD-L1",
        template_name="Field Sales Executive",
        category="permanent",
        designation_level=1,
        ctc_annual_default=Decimal("300000"),
        basic_amount=Decimal("12500"),
        hra_amount=Decimal("5000"),
        other_allowance=Decimal("1500"),
        conveyance=Decimal("5000"),
        has_probation=True,
        mediclaim_amount=Decimal("200000"),
        pa_insurance_amount=Decimal("500000"),
    ),
    dict(
        template_code="JKT-HOUSE-L1",
        template_name="Housekeeping Staff",
        category="permanent",
        designation_level=1,
        ctc_annual_default=Decimal("180000"),
        basic_amount=Decimal("9000"),
        hra_amount=Decimal("4500"),
        other_allowance=Decimal("1000"),
        has_probation=True,
        mediclaim_amount=Decimal("100000"),
        pa_insurance_amount=Decimal("300000"),
    ),
]


# Departments — extra ones beyond seed_auth.py
EXTRA_DEPARTMENTS = [
    ("IT", "IT"),
    ("Admin", "ADM"),
]


# (code, name, level, dept_code)
DESIGNATIONS = [
    ("DIR", "Director", 5, "ENG"),
    ("MGR", "Engineering Manager", 4, "ENG"),
    ("LEAD", "Tech Lead", 3, "IT"),
    ("DEV2", "Senior Developer", 2, "IT"),
    ("DEV1", "Junior Developer", 1, "IT"),
    ("HRMGR", "HR Manager", 4, "HR"),
    ("ADM1", "Admin Executive", 2, "ADM"),
    ("FE1", "Field Executive", 1, "SAL"),
    ("INT", "Intern", 1, "IT"),
]


# Sample employees. Only one entry: JKT001 hosts the super-admin login
# (admin@hrms.com) AND doubles as the real employee profile for
# Shyamveer Singh from the attendance spreadsheet. The other 11
# real employees (JKT002..JKT012) are seeded by
# scripts/seed_attendance_history.py from the spreadsheet — their
# names, DOJs, etc. live there as the source of truth.
#
# Earlier demo employees JKT014..JKT018 (HR Demo, Manager Demo, Employee
# Demo, Test Intern, Pooja Kumawat) were retired so the directory
# matches the actual headcount; the seed_attendance_history script
# cleans up any leftover Employee rows for those codes on first run.
SAMPLE_EMPLOYEES = [
    dict(
        employee_code="JKT001",
        first_name="Shyamveer", last_name="Singh",
        category_code="PERMANENT", template_code="JKT-PERM-L5",
        designation_code="DIR", department_code="ENG",
        date_of_joining=date(2024, 9, 14),
        date_of_birth=date(1991, 9, 11),
        ctc_annual=Decimal("3600000"),
        is_on_probation=False,
        confirmation_date=date(2025, 3, 14),
        user_email="admin@hrms.com",
    ),
]


async def seed_categories(db: AsyncSession) -> dict[str, EmployeeCategory]:
    existing = {
        c.code: c
        for c in (await db.execute(select(EmployeeCategory))).scalars().all()
    }
    for spec in CATEGORIES:
        c = existing.get(spec["code"])
        if not c:
            c = EmployeeCategory(**spec)
            db.add(c)
            existing[spec["code"]] = c
    await db.flush()
    return existing


async def seed_templates(db: AsyncSession) -> dict[str, SalaryTemplate]:
    existing = {
        t.template_code: t
        for t in (await db.execute(select(SalaryTemplate))).scalars().all()
    }
    for spec in SALARY_TEMPLATES:
        t = existing.get(spec["template_code"])
        if not t:
            t = SalaryTemplate(**spec)
            db.add(t)
            existing[spec["template_code"]] = t
    await db.flush()
    return existing


async def seed_extra_departments(db: AsyncSession) -> dict[str, Department]:
    existing = {
        d.code: d
        for d in (await db.execute(select(Department))).scalars().all()
    }
    for name, code in EXTRA_DEPARTMENTS:
        if code not in existing:
            d = Department(name=name, code=code)
            db.add(d)
            existing[code] = d
    await db.flush()
    return existing


async def seed_designations(
    db: AsyncSession, departments: dict[str, Department]
) -> dict[str, Designation]:
    existing = {
        d.code: d
        for d in (await db.execute(select(Designation))).scalars().all()
    }
    for code, name, level, dept_code in DESIGNATIONS:
        if code not in existing:
            d = Designation(
                code=code,
                name=name,
                level=level,
                department_id=departments[dept_code].id if dept_code in departments else None,
            )
            db.add(d)
            existing[code] = d
    await db.flush()
    return existing


async def _ensure_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    role_code: str,
) -> User:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password("changeme123"),
            is_active=True,
            is_admin_portal=False,
        )
        db.add(user)
        await db.flush()
    role = (
        await db.execute(select(Role).where(Role.code == role_code))
    ).scalar_one_or_none()
    if role and role.id not in {ur.role_id for ur in user.roles}:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.flush()
    return user


async def seed_employees(
    db: AsyncSession,
    categories: dict[str, EmployeeCategory],
    templates: dict[str, SalaryTemplate],
    departments: dict[str, Department],
    designations: dict[str, Designation],
) -> None:
    existing = {
        e.employee_code: e
        for e in (await db.execute(select(Employee))).scalars().all()
    }

    # First pass — create employees without manager links.
    for spec in SAMPLE_EMPLOYEES:
        if spec["employee_code"] in existing:
            continue

        user_id: int | None = None
        email = spec.get("user_email")
        if email:
            # Map user role from category (intern→intern, others→appropriate).
            cat = spec["category_code"]
            role_for_email = {
                "admin@hrms.com": "director",
                "hr@hrms.com": "hr",
                "manager@hrms.com": "manager",
                "employee@hrms.com": "employee",
            }.get(email, "employee")
            user = await _ensure_user(
                db, email, f"{spec['first_name']} {spec['last_name']}", role_for_email
            )
            user_id = user.id
        elif spec["category_code"] == "INTERN":
            # Create a dedicated user for the intern so they can log in.
            user = await _ensure_user(
                db,
                f"{spec['employee_code'].lower()}@jaikalki.com",
                f"{spec['first_name']} {spec['last_name']}",
                "intern",
            )
            user_id = user.id
        elif spec["employee_code"] == "JKT014":
            # Create Pooja's user too.
            user = await _ensure_user(
                db, "pooja@jaikalki.com",
                "Pooja Kumawat",
                "employee",
            )
            user_id = user.id

        emp = Employee(
            user_id=user_id,
            employee_code=spec["employee_code"],
            first_name=spec["first_name"],
            last_name=spec["last_name"],
            date_of_birth=spec.get("date_of_birth"),
            category_id=categories[spec["category_code"]].id,
            designation_id=designations[spec["designation_code"]].id
            if spec.get("designation_code") in designations
            else None,
            department_id=departments[spec["department_code"]].id
            if spec.get("department_code") in departments
            else None,
            salary_template_id=templates[spec["template_code"]].id,
            date_of_joining=spec["date_of_joining"],
            ctc_annual=spec.get("ctc_annual", Decimal("0")),
            is_on_probation=spec.get("is_on_probation", True),
            confirmation_date=spec.get("confirmation_date"),
            status="active",
        )
        # Probation end = joining + N months for those still on probation.
        if emp.is_on_probation:
            cat = categories[spec["category_code"]]
            if cat.requires_probation:
                # Avoid python-dateutil dependency: 30 days × N months.
                from datetime import timedelta
                emp.probation_end_date = emp.date_of_joining + timedelta(
                    days=30 * cat.default_probation_months
                )
        db.add(emp)
        await db.flush()
        existing[emp.employee_code] = emp

        # Probation tracker
        if emp.is_on_probation and emp.probation_end_date:
            db.add(
                EmployeeProbation(
                    employee_id=emp.id,
                    probation_start_date=emp.date_of_joining,
                    probation_end_date=emp.probation_end_date,
                    status="in_progress",
                )
            )

    await db.flush()

    # Second pass — wire managers.
    for spec in SAMPLE_EMPLOYEES:
        manager_code = spec.get("manager_code")
        if not manager_code:
            continue
        emp = existing.get(spec["employee_code"])
        manager = existing.get(manager_code)
        if emp and manager and emp.reporting_to is None:
            emp.reporting_to = manager.id
    await db.flush()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        categories = await seed_categories(db)
        templates = await seed_templates(db)
        departments = await seed_extra_departments(db)
        # Re-pull departments to include those from seed_auth.
        departments = {
            d.code: d
            for d in (await db.execute(select(Department))).scalars().all()
        }
        designations = await seed_designations(db, departments)
        await seed_employees(db, categories, templates, departments, designations)
        await db.commit()
    print("✔ Employees seeded")
    for spec in SAMPLE_EMPLOYEES:
        print(f"   - {spec['employee_code']:<8} {spec['first_name']} {spec['last_name']:<12} ({spec['category_code']})")


if __name__ == "__main__":
    asyncio.run(run())

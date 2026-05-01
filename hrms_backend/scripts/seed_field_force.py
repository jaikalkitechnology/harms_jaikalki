"""Seed field force module: customers, field employee (JKT019), today's jobs."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Customer,
    Department,
    Designation,
    Employee,
    EmployeeCategory,
    FieldEmployee,
    FieldJob,
    Role,
    SalaryTemplate,
    User,
    UserRole,
)
from app.core.security import hash_password


CUSTOMERS = [
    dict(
        name="Sai Hardware Mart",
        type="customer",
        address="Shop 12, MG Road",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        geo_lat=Decimal("12.9716000"),
        geo_lng=Decimal("77.5946000"),
        industry="Hardware retail",
        gst="29ABCDE1234F1Z5",
        pan="ABCDE1234F",
        territory="South-Bengaluru",
        contact_persons=[{"name": "Suresh", "phone": "+91-9000000001"}],
    ),
    dict(
        name="Apex Pharma Distributors",
        type="customer",
        address="Plot 45, Industrial Area",
        city="Bengaluru",
        state="Karnataka",
        pincode="560058",
        geo_lat=Decimal("13.0007000"),
        geo_lng=Decimal("77.5500000"),
        industry="Pharma",
        gst="29APEXP1234A1Z2",
        pan="APEXP1234A",
        territory="North-Bengaluru",
        contact_persons=[{"name": "Anita", "phone": "+91-9000000002"}],
    ),
    dict(
        name="GreenLeaf Cafe",
        type="prospect",
        address="2nd Cross, Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        pincode="560038",
        geo_lat=Decimal("12.9719000"),
        geo_lng=Decimal("77.6412000"),
        industry="F&B",
        territory="East-Bengaluru",
        contact_persons=[{"name": "Karthik", "phone": "+91-9000000003"}],
    ),
    dict(
        name="Vyom Electronics",
        type="lead",
        address="HSR Layout Sector 2",
        city="Bengaluru",
        state="Karnataka",
        pincode="560102",
        geo_lat=Decimal("12.9081000"),
        geo_lng=Decimal("77.6476000"),
        industry="Electronics",
        territory="South-Bengaluru",
        contact_persons=[{"name": "Vyom", "phone": "+91-9000000004"}],
    ),
]


async def _ensure_user(db: AsyncSession, email: str, name: str) -> User:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user:
        return user
    user = User(
        email=email,
        password_hash=hash_password("Password@123"),
        full_name=name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = (
        await db.execute(select(Role).where(Role.code == "field"))
    ).scalar_one_or_none()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.flush()
    return user


async def seed_field_employee(db: AsyncSession) -> Employee:
    code = "JKT019"
    emp = (
        await db.execute(select(Employee).where(Employee.employee_code == code))
    ).scalar_one_or_none()
    if emp:
        return emp

    user = await _ensure_user(db, "jkt019@jaikalki.com", "Ramesh Field")
    cat = (
        await db.execute(
            select(EmployeeCategory).where(EmployeeCategory.code == "PERMANENT")
        )
    ).scalar_one_or_none()
    template = (
        await db.execute(
            select(SalaryTemplate).where(SalaryTemplate.template_code == "JKT-FIELD-L1")
        )
    ).scalar_one_or_none()
    department = (
        await db.execute(select(Department).where(Department.code == "SAL"))
    ).scalar_one_or_none()
    designation = (
        await db.execute(select(Designation).where(Designation.code == "FE1"))
    ).scalar_one_or_none()

    emp = Employee(
        user_id=user.id,
        employee_code=code,
        first_name="Ramesh",
        last_name="Field",
        category_id=cat.id if cat else None,
        salary_template_id=template.id if template else None,
        department_id=department.id if department else None,
        designation_id=designation.id if designation else None,
        date_of_joining=date(2025, 11, 1),
        ctc_annual=Decimal("300000"),
        is_on_probation=False,
        confirmation_date=date(2026, 2, 1),
        status="active",
    )
    db.add(emp)
    await db.flush()

    fe = FieldEmployee(
        employee_id=emp.id,
        type="sales",
        territory="South-Bengaluru",
        vehicle_type="two_wheeler",
        vehicle_number="KA-01-AB-1234",
        license_number="KA0120240001234",
        current_status="idle",
        is_active=True,
    )
    db.add(fe)
    await db.flush()
    return emp


async def seed_customers(db: AsyncSession, created_by: int | None = None) -> list[Customer]:
    existing = {
        c.name: c
        for c in (await db.execute(select(Customer))).scalars().all()
    }
    out: list[Customer] = []
    for spec in CUSTOMERS:
        c = existing.get(spec["name"])
        if c:
            out.append(c)
            continue
        c = Customer(**spec, created_by=created_by, is_active=True)
        db.add(c)
        await db.flush()
        existing[c.name] = c
        out.append(c)
    return out


async def seed_jobs(
    db: AsyncSession, employee: Employee, customers: list[Customer]
) -> list[FieldJob]:
    today = date.today()
    existing = (
        await db.execute(
            select(FieldJob)
            .where(FieldJob.employee_id == employee.id)
            .where(FieldJob.scheduled_date == today)
        )
    ).scalars().all()
    if existing:
        return list(existing)

    jobs_specs = [
        dict(customer=customers[0], job_type="sales_call", scheduled_time="10:00", priority="high"),
        dict(customer=customers[1], job_type="demo", scheduled_time="12:00", priority="medium"),
        dict(customer=customers[2], job_type="collection", scheduled_time="15:00", priority="medium"),
        dict(customer=customers[3], job_type="survey", scheduled_time="17:00", priority="low"),
    ]
    out: list[FieldJob] = []
    for spec in jobs_specs:
        job = FieldJob(
            employee_id=employee.id,
            customer_id=spec["customer"].id,
            job_type=spec["job_type"],
            scheduled_date=today,
            scheduled_time=spec["scheduled_time"],
            priority=spec["priority"],
            status="scheduled",
            assigned_at=datetime.utcnow(),
        )
        db.add(job)
        out.append(job)
    await db.flush()
    return out


async def seed(db: AsyncSession) -> None:
    emp = await seed_field_employee(db)
    customers = await seed_customers(db, created_by=None)
    await seed_jobs(db, emp, customers)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Field force seeded (JKT019, 4 customers, 4 jobs)")


if __name__ == "__main__":
    asyncio.run(run())

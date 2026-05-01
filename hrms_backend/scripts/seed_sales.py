"""Seed sales: products, leads, sales target for JKT019."""
from __future__ import annotations

import asyncio
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Customer, Employee, Lead, Product, SalesTarget


PRODUCTS = [
    dict(
        sku="JKT-PROD-001",
        name="Smart Inverter 1.5kVA",
        description="Pure sine-wave inverter with 4-hour backup",
        category="Power",
        unit_price=Decimal("8499.00"),
        tax_pct=Decimal("18.00"),
    ),
    dict(
        sku="JKT-PROD-002",
        name="Lithium Battery 100Ah",
        description="LiFePO4 battery, 5-year warranty",
        category="Power",
        unit_price=Decimal("18999.00"),
        tax_pct=Decimal("18.00"),
    ),
    dict(
        sku="JKT-PROD-003",
        name="Solar Panel 320W Mono",
        description="Mono-crystalline panel, 25-year output guarantee",
        category="Solar",
        unit_price=Decimal("6499.00"),
        tax_pct=Decimal("18.00"),
    ),
    dict(
        sku="JKT-PROD-004",
        name="Smart Charge Controller 40A",
        description="MPPT charge controller with Bluetooth monitoring",
        category="Solar",
        unit_price=Decimal("4299.00"),
        tax_pct=Decimal("18.00"),
    ),
    dict(
        sku="JKT-SVC-AMC",
        name="Annual Maintenance Contract",
        description="Quarterly visits + remote support for 1 year",
        category="Services",
        unit_price=Decimal("2999.00"),
        tax_pct=Decimal("18.00"),
    ),
]


async def seed_products(db: AsyncSession) -> list[Product]:
    existing = {
        p.sku: p for p in (await db.execute(select(Product))).scalars().all()
    }
    out = []
    for spec in PRODUCTS:
        p = existing.get(spec["sku"])
        if p:
            out.append(p)
            continue
        p = Product(**spec, is_active=True)
        db.add(p)
        await db.flush()
        out.append(p)
    return out


async def seed_leads(db: AsyncSession) -> list[Lead]:
    """Seed a few leads tied to existing customers (created in seed_field_force)."""
    existing = (await db.execute(select(Lead))).scalars().all()
    if existing:
        return list(existing)

    # Find JKT019 (field employee) + customers
    emp = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT019")
        )
    ).scalar_one_or_none()
    customers = (await db.execute(select(Customer))).scalars().all()
    if not emp or not customers:
        return []

    today = date.today()
    specs = [
        dict(
            customer_id=customers[0].id,
            contact_name="Suresh",
            contact_phone="+91-9000000001",
            source="field_visit",
            stage="qualified",
            expected_value=Decimal("45000.00"),
            expected_close_date=today + timedelta(days=14),
            assigned_to=emp.id,
            score=50,
            next_action="Send proposal",
            next_action_date=today + timedelta(days=2),
            notes="Wants 1.5kVA inverter + 2 batteries",
        ),
        dict(
            customer_id=customers[1].id if len(customers) > 1 else customers[0].id,
            contact_name="Anita",
            contact_phone="+91-9000000002",
            source="referral",
            stage="proposal",
            expected_value=Decimal("120000.00"),
            expected_close_date=today + timedelta(days=21),
            assigned_to=emp.id,
            score=70,
            next_action="Demo on-site",
            next_action_date=today + timedelta(days=5),
        ),
        dict(
            customer_id=customers[2].id if len(customers) > 2 else customers[0].id,
            contact_name="Karthik",
            contact_phone="+91-9000000003",
            source="cold_call",
            stage="contacted",
            expected_value=Decimal("8499.00"),
            expected_close_date=today + timedelta(days=10),
            assigned_to=emp.id,
            score=25,
        ),
        dict(
            customer_id=customers[3].id if len(customers) > 3 else customers[0].id,
            contact_name="Vyom",
            contact_phone="+91-9000000004",
            source="exhibition",
            stage="new",
            expected_value=Decimal("25000.00"),
            assigned_to=emp.id,
            score=10,
        ),
    ]
    out = []
    for spec in specs:
        lead = Lead(**spec)
        db.add(lead)
        await db.flush()
        out.append(lead)
    return out


async def seed_target(db: AsyncSession) -> None:
    """Monthly sales target for JKT019."""
    emp = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT019")
        )
    ).scalar_one_or_none()
    if not emp:
        return
    today = date.today()
    period_start = today.replace(day=1)
    # Last day of month
    if period_start.month == 12:
        next_month = period_start.replace(year=period_start.year + 1, month=1)
    else:
        next_month = period_start.replace(month=period_start.month + 1)
    period_end = next_month - timedelta(days=1)

    existing = (
        await db.execute(
            select(SalesTarget)
            .where(SalesTarget.employee_id == emp.id)
            .where(SalesTarget.period_start == period_start)
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(
        SalesTarget(
            employee_id=emp.id,
            period_type="monthly",
            period_start=period_start,
            period_end=period_end,
            target_amount=Decimal("250000.00"),
            achieved_amount=Decimal("0"),
            commission_pct=Decimal("3.00"),
            notes="Monthly target — Bengaluru South territory",
        )
    )
    await db.flush()


async def seed(db: AsyncSession) -> None:
    await seed_products(db)
    await seed_leads(db)
    await seed_target(db)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Sales seeded (products, leads, target)")


if __name__ == "__main__":
    asyncio.run(run())

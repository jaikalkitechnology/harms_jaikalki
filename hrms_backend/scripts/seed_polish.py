"""Seed polish features: 5 assets, 3 meeting rooms, 1 published job posting."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Asset,
    AssetAssignment,
    Department,
    Employee,
    JobPosting,
    MeetingRoom,
)


ASSETS = [
    dict(
        asset_tag="JKT-LAP-001",
        name="MacBook Pro 14 M3",
        category="laptop",
        serial_number="MBP-14-001",
        purchase_date=date(2025, 11, 1),
        purchase_cost=Decimal("199000.00"),
        warranty_until=date(2028, 11, 1),
        condition="good",
    ),
    dict(
        asset_tag="JKT-LAP-002",
        name="Dell Latitude 7440",
        category="laptop",
        serial_number="DELL-7440-002",
        purchase_date=date(2025, 9, 15),
        purchase_cost=Decimal("125000.00"),
        warranty_until=date(2028, 9, 15),
        condition="good",
    ),
    dict(
        asset_tag="JKT-MOB-001",
        name="iPhone 15 (Field)",
        category="mobile",
        serial_number="APL-IP15-001",
        purchase_date=date(2026, 1, 10),
        purchase_cost=Decimal("85000.00"),
        warranty_until=date(2027, 1, 10),
        condition="new",
    ),
    dict(
        asset_tag="JKT-HDS-001",
        name="Sony WH-1000XM5",
        category="headset",
        serial_number="SNY-XM5-001",
        purchase_date=date(2025, 12, 5),
        purchase_cost=Decimal("28000.00"),
        condition="new",
    ),
    dict(
        asset_tag="JKT-VEH-001",
        name="Royal Enfield Bullet 350",
        category="vehicle",
        serial_number="RE-BLT-350-001",
        purchase_date=date(2025, 8, 20),
        purchase_cost=Decimal("190000.00"),
        condition="good",
    ),
]


ROOMS = [
    dict(
        code="JKT-MR-01",
        name="Sea View",
        location="2nd floor, west wing",
        capacity=8,
        has_video=True,
    ),
    dict(
        code="JKT-MR-02",
        name="Boardroom",
        location="3rd floor",
        capacity=14,
        has_video=True,
    ),
    dict(
        code="JKT-HUDDLE-01",
        name="Huddle 1",
        location="2nd floor, near pantry",
        capacity=4,
        has_video=False,
    ),
]


async def seed_assets(db: AsyncSession) -> None:
    existing = (
        await db.execute(select(Asset))
    ).scalars().all()
    if existing:
        return
    field_emp = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT019")
        )
    ).scalar_one_or_none()
    employee_demo = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT018")
        )
    ).scalar_one_or_none()

    created: list[Asset] = []
    for spec in ASSETS:
        a = Asset(**spec, status="in_stock")
        db.add(a)
        await db.flush()
        created.append(a)

    # Assign one laptop to JKT018 and the field-tagged mobile + bike to JKT019.
    if employee_demo and len(created) >= 2:
        a = created[1]
        a.status = "assigned"
        a.assigned_to = employee_demo.id
        a.assigned_at = datetime.utcnow()
        db.add(
            AssetAssignment(
                asset_id=a.id,
                employee_id=employee_demo.id,
                assigned_at=datetime.utcnow(),
                notes="Issued at onboarding",
            )
        )
    if field_emp:
        for tag in ("JKT-MOB-001", "JKT-VEH-001"):
            asset = next((a for a in created if a.asset_tag == tag), None)
            if asset:
                asset.status = "assigned"
                asset.assigned_to = field_emp.id
                asset.assigned_at = datetime.utcnow()
                db.add(
                    AssetAssignment(
                        asset_id=asset.id,
                        employee_id=field_emp.id,
                        assigned_at=datetime.utcnow(),
                        notes="Field kit",
                    )
                )
    await db.flush()


async def seed_rooms(db: AsyncSession) -> None:
    existing = (await db.execute(select(MeetingRoom))).scalars().all()
    if existing:
        return
    for spec in ROOMS:
        db.add(MeetingRoom(**spec, is_active=True))
    await db.flush()


async def seed_postings(db: AsyncSession) -> None:
    existing = (
        await db.execute(
            select(JobPosting).where(JobPosting.code == "JKT-IJP-DEV-001")
        )
    ).scalar_one_or_none()
    if existing:
        return
    it_dept = (
        await db.execute(
            select(Department).where(Department.code == "IT")
        )
    ).scalar_one_or_none()
    posting = JobPosting(
        code="JKT-IJP-DEV-001",
        title="Senior Backend Engineer",
        department_id=it_dept.id if it_dept else None,
        location="Bengaluru / Hybrid",
        employment_type="full_time",
        description=(
            "Own backend services for HRMS modules — Python + FastAPI + "
            "MySQL. Mentor juniors, drive p90 latency targets, partner with "
            "the field force PM."
        ),
        requirements=(
            "5+ years in Python, strong SQL, hands-on with async/await."
        ),
        referral_bonus=Decimal("50000.00"),
        is_internal_only=True,
        posted_at=datetime.utcnow(),
        closes_on=date.today() + timedelta(days=21),
        status="published",
    )
    db.add(posting)
    await db.flush()


async def seed(db: AsyncSession) -> None:
    await seed_assets(db)
    await seed_rooms(db)
    await seed_postings(db)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Polish seeded (5 assets, 3 rooms, 1 IJP)")


if __name__ == "__main__":
    asyncio.run(run())

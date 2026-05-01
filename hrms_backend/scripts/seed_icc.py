"""Seed a baseline POSH-compliant ICC committee.

Idempotent. Run after seed_employees.py.
"""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import IccMember


MEMBERS = [
    dict(
        member_name="Anita Sharma",
        role="presiding_officer",
        gender="female",
        is_external=False,
        contact="anita.sharma@jaikalki.com",
    ),
    dict(
        member_name="Priya Iyer",
        role="member",
        gender="female",
        is_external=False,
        contact="priya.iyer@jaikalki.com",
    ),
    dict(
        member_name="Ravi Kumar",
        role="member",
        gender="male",
        is_external=False,
        contact="ravi.kumar@jaikalki.com",
    ),
    dict(
        member_name="Adv. Sushma Pillai",
        role="external_member",
        gender="female",
        is_external=True,
        contact="sushma@example-law.in",
    ),
]


async def seed(db: AsyncSession) -> None:
    existing = {
        m.member_name: m
        for m in (await db.execute(select(IccMember))).scalars().all()
    }
    today = date.today()
    for spec in MEMBERS:
        if spec["member_name"] in existing:
            continue
        db.add(
            IccMember(
                **spec,
                term_start=today,
                is_active=True,
            )
        )
    await db.flush()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print(f"✔ Seeded {len(MEMBERS)} ICC members")


if __name__ == "__main__":
    asyncio.run(run())

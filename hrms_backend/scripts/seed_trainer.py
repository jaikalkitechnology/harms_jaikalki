"""Seed trainer module: 2 trainers + 2 upcoming sessions."""
from __future__ import annotations

import asyncio
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Course,
    Employee,
    TrainerProfile,
    TrainingSession,
)


async def seed_trainers(db: AsyncSession) -> list[TrainerProfile]:
    existing = (
        await db.execute(select(TrainerProfile))
    ).scalars().all()
    if existing:
        return list(existing)

    # Internal: HR demo employee
    hr_emp = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT015")
        )
    ).scalar_one_or_none()

    out: list[TrainerProfile] = []
    if hr_emp:
        internal = TrainerProfile(
            employee_id=hr_emp.id,
            is_external=False,
            full_name=f"{hr_emp.first_name} {hr_emp.last_name}",
            headline="HR Manager · POSH-certified facilitator",
            bio=(
                "Leads onboarding, POSH and people-leadership programs at "
                "Jaikalki. 8+ years in HR with a focus on inclusive workplaces."
            ),
            languages=["English", "Hindi"],
            specializations=[
                "POSH",
                "Onboarding",
                "Leadership",
                "Soft skills",
            ],
            years_experience=8,
            hourly_rate=Decimal("0"),
            is_active=True,
        )
        db.add(internal)
        await db.flush()
        out.append(internal)

    # External
    external = TrainerProfile(
        is_external=True,
        full_name="Vikram Singh",
        headline="Field Sales Coach · ex-Schneider, ex-Luminous",
        bio=(
            "Specialises in field sales playbooks, objection handling, and "
            "B2B distribution. Trained 2,000+ sales executives across India."
        ),
        contact_email="vikram@trainer.example.com",
        contact_phone="+91-9000000099",
        languages=["English", "Hindi", "Punjabi"],
        specializations=["Field Sales", "Negotiation", "B2B", "Distribution"],
        years_experience=14,
        hourly_rate=Decimal("4500.00"),
        is_active=True,
    )
    db.add(external)
    await db.flush()
    out.append(external)

    return out


async def seed_sessions(
    db: AsyncSession, trainers: list[TrainerProfile]
) -> None:
    if not trainers:
        return
    existing = (await db.execute(select(TrainingSession))).scalars().all()
    if existing:
        return

    courses = (await db.execute(select(Course))).scalars().all()
    by_code = {c.code: c for c in courses}

    now = datetime.utcnow().replace(microsecond=0)

    posh_session = TrainingSession(
        code="JKT-TS-POSH-001",
        title="Live POSH Refresher",
        description=(
            "Open Q&A + scenario walkthroughs to complement the POSH "
            "self-paced course."
        ),
        trainer_id=trainers[0].id,
        course_id=by_code.get("JKT-LMS-POSH-2026").id
        if by_code.get("JKT-LMS-POSH-2026")
        else None,
        session_type="virtual",
        scheduled_start=now + timedelta(days=2, hours=4),
        scheduled_end=now + timedelta(days=2, hours=5, minutes=30),
        timezone="Asia/Kolkata",
        meeting_url="https://meet.example.com/posh-refresher",
        capacity=80,
        qr_token=secrets.token_urlsafe(16),
        status="open_for_registration",
    )
    db.add(posh_session)

    sales_session = TrainingSession(
        code="JKT-TS-FIELD-001",
        title="Field Sales 101 — Live Workshop",
        description=(
            "Hands-on workshop with role-plays for the Bengaluru field team."
        ),
        trainer_id=trainers[-1].id,
        course_id=by_code.get("JKT-LMS-FIELD-101").id
        if by_code.get("JKT-LMS-FIELD-101")
        else None,
        session_type="hybrid",
        scheduled_start=now + timedelta(days=5, hours=3),
        scheduled_end=now + timedelta(days=5, hours=6),
        timezone="Asia/Kolkata",
        location="Jaikalki Office, Bengaluru",
        meeting_url="https://meet.example.com/field-sales-101",
        capacity=25,
        qr_token=secrets.token_urlsafe(16),
        status="open_for_registration",
    )
    db.add(sales_session)
    await db.flush()


async def seed(db: AsyncSession) -> None:
    trainers = await seed_trainers(db)
    await seed_sessions(db, trainers)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Trainer module seeded (2 trainers, 2 sessions)")


if __name__ == "__main__":
    asyncio.run(run())

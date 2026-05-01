"""Seed performance: 1 active cycle + sample goals for the demo employee."""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Employee, Goal, ReviewCycle


async def seed_cycle(db: AsyncSession) -> ReviewCycle:
    existing = (
        await db.execute(
            select(ReviewCycle).where(ReviewCycle.code == "Q2-2026")
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    today = date.today()
    quarter_start = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)
    if quarter_start.month + 3 > 12:
        quarter_end = date(quarter_start.year, 12, 31)
    else:
        from calendar import monthrange

        last_month = quarter_start.month + 2
        last_day = monthrange(quarter_start.year, last_month)[1]
        quarter_end = date(quarter_start.year, last_month, last_day)

    cycle = ReviewCycle(
        code="Q2-2026",
        name="Q2 2026 Performance Review",
        cycle_type="quarterly",
        period_start=quarter_start,
        period_end=quarter_end,
        self_review_due=quarter_end + timedelta(days=7),
        manager_review_due=quarter_end + timedelta(days=14),
        calibration_due=quarter_end + timedelta(days=21),
        status="open",
    )
    db.add(cycle)
    await db.flush()
    return cycle


async def seed_goals(db: AsyncSession, cycle: ReviewCycle) -> None:
    emp = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT018")
        )
    ).scalar_one_or_none()
    if not emp:
        return
    existing = (
        await db.execute(
            select(Goal)
            .where(Goal.employee_id == emp.id)
            .where(Goal.cycle_id == cycle.id)
        )
    ).scalars().all()
    if existing:
        return
    specs = [
        dict(
            title="Ship the V2 attendance redesign",
            description=(
                "Lead the engineering side of the new attendance dashboard, "
                "including geo-fence + selfie flows."
            ),
            metric="Production launch",
            target_value="GA by quarter end",
            weight_pct=40,
            category="business",
            due_date=cycle.period_end,
            status="active",
        ),
        dict(
            title="Mentor 2 junior developers through their probation",
            description=(
                "Weekly 1-on-1s + paired code reviews + clear feedback loops."
            ),
            metric="Confirmation pass rate",
            target_value="2 of 2 pass on time",
            weight_pct=30,
            category="people",
            due_date=cycle.period_end,
            status="active",
        ),
        dict(
            title="Complete POSH certification",
            description="Mandatory annual POSH certification.",
            metric="Score",
            target_value=">= 80%",
            weight_pct=10,
            category="growth",
            due_date=cycle.period_end - timedelta(days=14),
            status="active",
        ),
        dict(
            title="Drive p90 API latency below 350ms",
            description="Optimise the field-force live-map and team-performance queries.",
            metric="p90 latency",
            target_value="<= 350ms",
            weight_pct=20,
            category="operational",
            due_date=cycle.period_end,
            status="active",
        ),
    ]
    for spec in specs:
        db.add(Goal(employee_id=emp.id, cycle_id=cycle.id, **spec))
    await db.flush()


async def seed(db: AsyncSession) -> None:
    cycle = await seed_cycle(db)
    await seed_goals(db, cycle)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Performance seeded (Q2-2026 cycle + 4 goals for JKT018)")


if __name__ == "__main__":
    asyncio.run(run())

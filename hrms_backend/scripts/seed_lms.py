"""Seed LMS: 3 courses (onboarding, compliance, technical), 5 badges."""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Badge,
    Course,
    CourseLesson,
    CourseModule,
)


COURSES = [
    dict(
        code="JKT-LMS-ONB-101",
        title="Welcome to Jaikalki",
        description="Your first week orientation: company values, products, "
        "code of conduct, key contacts.",
        category="onboarding",
        difficulty="beginner",
        estimated_hours=4,
        is_mandatory=True,
        validity_months=None,
        points=50,
        modules=[
            dict(
                title="Company introduction",
                sort_order=0,
                lessons=[
                    dict(
                        title="Our story & values",
                        content_type="article",
                        article_body=(
                            "Jaikalki Technology Pvt Ltd was founded with a "
                            "mission to deliver power, mobility and verification "
                            "services across India. Our values: trust, craftsmanship "
                            "and customer obsession."
                        ),
                        duration_minutes=10,
                        sort_order=0,
                        points=2,
                    ),
                    dict(
                        title="Org chart & key contacts",
                        content_type="pdf",
                        content_url="https://example.com/org-chart.pdf",
                        duration_minutes=8,
                        sort_order=1,
                        points=2,
                    ),
                ],
            ),
            dict(
                title="Tools & platforms",
                sort_order=1,
                lessons=[
                    dict(
                        title="Using the HRMS",
                        content_type="video",
                        content_url="https://example.com/hrms-walkthrough.mp4",
                        duration_minutes=15,
                        sort_order=0,
                        points=3,
                    ),
                    dict(
                        title="Email + Slack etiquette",
                        content_type="article",
                        article_body=(
                            "Reply to internal emails within one business day. "
                            "Use threads in Slack. Keep customer-facing emails "
                            "professional and on-brand."
                        ),
                        duration_minutes=8,
                        sort_order=1,
                        points=1,
                    ),
                ],
            ),
        ],
    ),
    dict(
        code="JKT-LMS-POSH-2026",
        title="POSH Awareness 2026",
        description="Mandatory annual training on Prevention of Sexual "
        "Harassment, ICC procedures, and your rights as an employee.",
        category="compliance",
        difficulty="beginner",
        estimated_hours=2,
        is_mandatory=True,
        validity_months=12,
        points=80,
        modules=[
            dict(
                title="What POSH covers",
                sort_order=0,
                lessons=[
                    dict(
                        title="Definitions & scope",
                        content_type="article",
                        article_body=(
                            "POSH applies at the workplace and at any work-related "
                            "location, including off-site events and online channels. "
                            "It protects all employees regardless of gender."
                        ),
                        duration_minutes=12,
                        sort_order=0,
                        points=4,
                    ),
                    dict(
                        title="The ICC process",
                        content_type="video",
                        content_url="https://example.com/posh-icc.mp4",
                        duration_minutes=18,
                        sort_order=1,
                        points=6,
                    ),
                ],
            ),
            dict(
                title="Reporting & resources",
                sort_order=1,
                lessons=[
                    dict(
                        title="How to report a complaint",
                        content_type="article",
                        article_body=(
                            "Use the Justice Portal in the HRMS. Reports can be "
                            "anonymous, confidential or open. Retaliation against "
                            "anyone who reports is itself a serious offence."
                        ),
                        duration_minutes=10,
                        sort_order=0,
                        points=4,
                    ),
                ],
            ),
        ],
    ),
    dict(
        code="JKT-LMS-FIELD-101",
        title="Field Selling 101",
        description="For field employees: customer mapping, the visit funnel, "
        "objection handling, and closing techniques.",
        category="technical",
        difficulty="intermediate",
        estimated_hours=6,
        is_mandatory=False,
        points=120,
        modules=[
            dict(
                title="The Jaikalki visit",
                sort_order=0,
                lessons=[
                    dict(
                        title="Before the visit: prep & target",
                        content_type="article",
                        article_body=(
                            "Pull the customer card from the CRM. Note last 3 "
                            "interactions and any pending complaints. Aim for one "
                            "concrete outcome per visit."
                        ),
                        duration_minutes=12,
                        sort_order=0,
                        points=3,
                    ),
                    dict(
                        title="During the visit: probing questions",
                        content_type="video",
                        content_url="https://example.com/probing.mp4",
                        duration_minutes=20,
                        sort_order=1,
                        points=5,
                    ),
                    dict(
                        title="After the visit: follow-up",
                        content_type="article",
                        article_body=(
                            "Send a thank-you note within 6 hours. Update the CRM "
                            "with the next action and date. If a quote is needed, "
                            "send it within 24 hours."
                        ),
                        duration_minutes=10,
                        sort_order=2,
                        points=3,
                    ),
                ],
            ),
        ],
    ),
]

BADGES = [
    dict(
        code="FIRST-LESSON",
        name="First Lesson",
        description="Completed your first lesson",
        icon="🌱",
        points_required=1,
        courses_required=0,
        streak_days_required=0,
        tier="bronze",
    ),
    dict(
        code="ONBOARDED",
        name="Onboarded",
        description="Finished the Welcome to Jaikalki course",
        icon="🎓",
        points_required=50,
        courses_required=1,
        streak_days_required=0,
        tier="silver",
    ),
    dict(
        code="STREAK-7",
        name="Week-long Learner",
        description="Studied 7 days in a row",
        icon="🔥",
        points_required=0,
        courses_required=0,
        streak_days_required=7,
        tier="silver",
    ),
    dict(
        code="POSH-CERTIFIED",
        name="POSH Certified",
        description="Cleared mandatory POSH training",
        icon="🛡️",
        points_required=80,
        courses_required=2,
        streak_days_required=0,
        tier="gold",
    ),
    dict(
        code="POWER-LEARNER",
        name="Power Learner",
        description="Earned 500+ learning points",
        icon="⚡",
        points_required=500,
        courses_required=0,
        streak_days_required=0,
        tier="platinum",
    ),
]


async def seed_courses(db: AsyncSession) -> list[Course]:
    existing = {
        c.code: c for c in (await db.execute(select(Course))).scalars().all()
    }
    out = []
    for spec in COURSES:
        if spec["code"] in existing:
            out.append(existing[spec["code"]])
            continue
        modules_data = spec.pop("modules", [])
        course = Course(**spec, is_published=True)
        db.add(course)
        await db.flush()
        for m in modules_data:
            lessons = m.pop("lessons", [])
            module = CourseModule(course_id=course.id, **m)
            db.add(module)
            await db.flush()
            for l in lessons:
                db.add(CourseLesson(module_id=module.id, **l))
        out.append(course)
        # Restore key for repeated runs (we mutated the dict)
        spec["modules"] = modules_data
    await db.flush()
    return out


async def seed_badges(db: AsyncSession) -> list[Badge]:
    existing = {
        b.code: b for b in (await db.execute(select(Badge))).scalars().all()
    }
    out = []
    for spec in BADGES:
        b = existing.get(spec["code"])
        if not b:
            b = Badge(**spec)
            db.add(b)
            await db.flush()
        out.append(b)
    return out


async def seed(db: AsyncSession) -> None:
    await seed_courses(db)
    await seed_badges(db)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ LMS seeded (3 courses, 5 badges)")


if __name__ == "__main__":
    asyncio.run(run())

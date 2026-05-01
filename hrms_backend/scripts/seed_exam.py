"""Seed exams: question bank for POSH course + a certification exam."""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Course, Exam, ExamQuestion, QuestionBank, QuestionOption


POSH_QUESTIONS = [
    dict(
        question_text=(
            "Which of the following is covered under the POSH Act?"
        ),
        question_type="multiple_choice",
        topic="POSH Basics",
        difficulty="easy",
        marks=2,
        time_seconds=45,
        explanation=(
            "POSH covers physical, verbal and digital workplace harassment, "
            "and also off-site work events."
        ),
        options=[
            dict(option_text="In-office unwelcome physical contact",
                 is_correct=True, sort_order=0),
            dict(option_text="Inappropriate jokes in a Slack channel",
                 is_correct=True, sort_order=1),
            dict(option_text="Personal medical history of an employee",
                 is_correct=False, sort_order=2),
            dict(option_text="Harassment at off-site team events",
                 is_correct=True, sort_order=3),
        ],
    ),
    dict(
        question_text=(
            "Where should an aggrieved employee report a POSH complaint at "
            "Jaikalki?"
        ),
        question_type="single_choice",
        topic="POSH Reporting",
        difficulty="easy",
        marks=2,
        time_seconds=30,
        explanation="Use the Justice Portal in the HRMS to file with the ICC.",
        options=[
            dict(option_text="The Justice Portal in the HRMS",
                 is_correct=True, sort_order=0),
            dict(option_text="Public social media",
                 is_correct=False, sort_order=1),
            dict(option_text="Their manager only",
                 is_correct=False, sort_order=2),
            dict(option_text="External police only",
                 is_correct=False, sort_order=3),
        ],
    ),
    dict(
        question_text=(
            "True or false: Retaliation against a complainant is itself a "
            "POSH violation."
        ),
        question_type="true_false",
        topic="POSH Reporting",
        difficulty="easy",
        marks=1,
        time_seconds=20,
        options=[
            dict(option_text="True", is_correct=True, sort_order=0),
            dict(option_text="False", is_correct=False, sort_order=1),
        ],
    ),
    dict(
        question_text=(
            "What is the recommended timeline for the ICC to acknowledge a "
            "complaint after submission?"
        ),
        question_type="single_choice",
        topic="ICC Process",
        difficulty="medium",
        marks=2,
        time_seconds=40,
        options=[
            dict(option_text="Within 2 working days",
                 is_correct=True, sort_order=0),
            dict(option_text="Within 30 working days",
                 is_correct=False, sort_order=1),
            dict(option_text="Within the same hour",
                 is_correct=False, sort_order=2),
            dict(option_text="No fixed timeline",
                 is_correct=False, sort_order=3),
        ],
    ),
    dict(
        question_text=(
            "Privacy levels available when filing a Justice complaint at "
            "Jaikalki include all of the following EXCEPT:"
        ),
        question_type="single_choice",
        topic="POSH Reporting",
        difficulty="medium",
        marks=2,
        time_seconds=40,
        options=[
            dict(option_text="Anonymous", is_correct=False, sort_order=0),
            dict(option_text="Confidential", is_correct=False, sort_order=1),
            dict(option_text="Open", is_correct=False, sort_order=2),
            dict(
                option_text="Public-by-default to all employees",
                is_correct=True,
                sort_order=3,
            ),
        ],
    ),
]


async def seed_questions(db: AsyncSession) -> list[QuestionBank]:
    existing = (await db.execute(select(QuestionBank))).scalars().all()
    existing_texts = {q.question_text for q in existing}
    out = list(existing)
    for spec in POSH_QUESTIONS:
        if spec["question_text"] in existing_texts:
            continue
        opts = spec.pop("options", [])
        q = QuestionBank(**spec, status="active")
        db.add(q)
        await db.flush()
        for o in opts:
            db.add(QuestionOption(question_id=q.id, **o))
        # Restore the dict key for any subsequent iterations
        spec["options"] = opts
        out.append(q)
    await db.flush()
    return out


async def seed_exam(
    db: AsyncSession, questions: list[QuestionBank]
) -> Exam | None:
    existing = (
        await db.execute(
            select(Exam).where(Exam.code == "JKT-EXAM-POSH-2026")
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    posh_course = (
        await db.execute(
            select(Course).where(Course.code == "JKT-LMS-POSH-2026")
        )
    ).scalar_one_or_none()
    if not posh_course:
        return None
    posh_qs = [
        q for q in questions if q.topic and "POSH" in (q.topic or "") or
        q.topic in ("ICC Process", "POSH Basics", "POSH Reporting")
    ]
    if not posh_qs:
        return None

    exam = Exam(
        code="JKT-EXAM-POSH-2026",
        title="POSH Certification Exam 2026",
        description="Mandatory annual certification quiz for all employees.",
        course_id=posh_course.id,
        exam_type="certification",
        total_questions=min(5, len(posh_qs)),
        time_limit_minutes=10,
        passing_percentage=70,
        question_selection="fixed",
        shuffle_questions=True,
        shuffle_options=True,
        attempts_allowed=3,
        cooldown_hours=2,
        negative_marking=False,
        validity_months=12,
        is_published=True,
    )
    db.add(exam)
    await db.flush()
    for i, q in enumerate(posh_qs):
        db.add(
            ExamQuestion(exam_id=exam.id, question_id=q.id, sort_order=i)
        )
    await db.flush()
    return exam


async def seed(db: AsyncSession) -> None:
    qs = await seed_questions(db)
    await seed_exam(db, qs)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Exam seeded (5 POSH questions + certification exam)")


if __name__ == "__main__":
    asyncio.run(run())

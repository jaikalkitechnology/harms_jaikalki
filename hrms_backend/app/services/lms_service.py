"""LMS service: courses, enrollment, progress, gamification."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Badge,
    Course,
    CourseEnrollment,
    CourseLesson,
    CourseModule,
    Employee,
    EmployeeBadge,
    EmployeeLearningStat,
    LessonProgress,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    return _now().date()


# Tier thresholds (points)
LEVEL_THRESHOLDS = [
    ("platinum", 1000),
    ("gold", 500),
    ("silver", 100),
    ("bronze", 0),
]


def _level_for_points(points: int) -> str:
    for level, threshold in LEVEL_THRESHOLDS:
        if points >= threshold:
            return level
    return "bronze"


# ── Course CRUD ──────────────────────────────────────────────────────
async def create_course(
    db: AsyncSession,
    *,
    payload: dict,
    created_by: Optional[int] = None,
) -> Course:
    if (
        await db.execute(select(Course).where(Course.code == payload["code"]))
    ).scalar_one_or_none():
        raise ConflictError(f"Course code '{payload['code']}' already exists")

    modules_payload = payload.pop("modules", [])
    course = Course(**payload, is_published=False, created_by=created_by)
    db.add(course)
    await db.flush()

    for m in modules_payload:
        m_data = m.model_dump() if hasattr(m, "model_dump") else dict(m)
        lessons_data = m_data.pop("lessons", [])
        module = CourseModule(course_id=course.id, **m_data)
        db.add(module)
        await db.flush()
        for ld in lessons_data:
            ld_data = ld.model_dump() if hasattr(ld, "model_dump") else dict(ld)
            db.add(CourseLesson(module_id=module.id, **ld_data))

    await db.commit()
    await db.refresh(course)
    return course


async def list_courses(
    db: AsyncSession,
    *,
    category: Optional[str] = None,
    department_id: Optional[int] = None,
    mandatory_only: bool = False,
    published_only: bool = True,
    limit: int = 200,
) -> Sequence[Course]:
    stmt = select(Course)
    if published_only:
        stmt = stmt.where(Course.is_published.is_(True))
    if category:
        stmt = stmt.where(Course.category == category)
    if department_id is not None:
        stmt = stmt.where(Course.department_id == department_id)
    if mandatory_only:
        stmt = stmt.where(Course.is_mandatory.is_(True))
    stmt = stmt.order_by(Course.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    # Decorate with question / exam counts so the admin UI can show
    # "12 Qs · 1 exam" on each card without N+1 round-trips.
    # Tolerant of an un-migrated DB: if the COUNT query fails (e.g.
    # the new exam_questions.course_id column hasn't been ALTERed in
    # yet), we fall back to zero counts and keep the page usable.
    if rows:
        from sqlalchemy import func
        from app.models import Exam, QuestionBank

        ids = [r.id for r in rows]
        try:
            q_counts = dict(
                (
                    await db.execute(
                        select(QuestionBank.course_id, func.count(QuestionBank.id))
                        .where(QuestionBank.course_id.in_(ids))
                        .group_by(QuestionBank.course_id)
                    )
                ).all()
            )
        except Exception:
            await db.rollback()
            q_counts = {}
        try:
            e_counts = dict(
                (
                    await db.execute(
                        select(Exam.course_id, func.count(Exam.id))
                        .where(Exam.course_id.in_(ids))
                        .group_by(Exam.course_id)
                    )
                ).all()
            )
        except Exception:
            await db.rollback()
            e_counts = {}
        for r in rows:
            # Transient attrs — Pydantic from_attributes picks them up.
            r.question_count = q_counts.get(r.id, 0)
            r.exam_count = e_counts.get(r.id, 0)
    return rows


async def get_course(db: AsyncSession, course_id: int) -> Course:
    course = (
        await db.execute(select(Course).where(Course.id == course_id))
    ).scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    return course


async def publish_course(
    db: AsyncSession, course_id: int, *, is_published: bool
) -> Course:
    course = await get_course(db, course_id)
    if is_published and not course.modules:
        raise ValidationError("Cannot publish a course without modules")
    course.is_published = is_published
    await db.commit()
    await db.refresh(course)
    return course


async def add_module(
    db: AsyncSession, course_id: int, *, payload: dict
) -> CourseModule:
    course = await get_course(db, course_id)
    lessons_data = payload.pop("lessons", [])
    module = CourseModule(course_id=course.id, **payload)
    db.add(module)
    await db.flush()
    for ld in lessons_data:
        ld_data = ld.model_dump() if hasattr(ld, "model_dump") else dict(ld)
        db.add(CourseLesson(module_id=module.id, **ld_data))
    await db.commit()
    await db.refresh(module)
    return module


async def add_lesson(
    db: AsyncSession, module_id: int, *, payload: dict
) -> CourseLesson:
    module = (
        await db.execute(
            select(CourseModule).where(CourseModule.id == module_id)
        )
    ).scalar_one_or_none()
    if not module:
        raise NotFoundError("Module not found")
    lesson = CourseLesson(module_id=module.id, **payload)
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


# ── Enrollment ────────────────────────────────────────────────────────
async def enroll(
    db: AsyncSession,
    *,
    course_id: int,
    employee: Employee,
    due_date: Optional[date] = None,
) -> CourseEnrollment:
    course = await get_course(db, course_id)
    if not course.is_published:
        raise ValidationError("Course is not published")
    existing = (
        await db.execute(
            select(CourseEnrollment)
            .where(CourseEnrollment.employee_id == employee.id)
            .where(CourseEnrollment.course_id == course_id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    enrollment = CourseEnrollment(
        employee_id=employee.id,
        course_id=course_id,
        enrolled_at=_now(),
        due_date=due_date,
        status="enrolled",
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def list_my_enrollments(
    db: AsyncSession,
    employee_id: int,
    *,
    status: Optional[str] = None,
) -> Sequence[CourseEnrollment]:
    stmt = select(CourseEnrollment).where(
        CourseEnrollment.employee_id == employee_id
    )
    if status:
        stmt = stmt.where(CourseEnrollment.status == status)
    stmt = stmt.order_by(CourseEnrollment.enrolled_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_enrollment(
    db: AsyncSession, enrollment_id: int
) -> CourseEnrollment:
    e = (
        await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.id == enrollment_id
            )
        )
    ).scalar_one_or_none()
    if not e:
        raise NotFoundError("Enrollment not found")
    return e


# ── Lesson progress ─────────────────────────────────────────────────
async def _all_lesson_ids_for_course(
    db: AsyncSession, course_id: int
) -> list[int]:
    rows = (
        await db.execute(
            select(CourseLesson.id)
            .join(CourseModule, CourseModule.id == CourseLesson.module_id)
            .where(CourseModule.course_id == course_id)
        )
    ).scalars().all()
    return list(rows)


async def complete_lesson(
    db: AsyncSession,
    *,
    employee: Employee,
    lesson_id: int,
    time_spent_seconds: int = 0,
    notes: Optional[str] = None,
) -> LessonProgress:
    lesson = (
        await db.execute(
            select(CourseLesson).where(CourseLesson.id == lesson_id)
        )
    ).scalar_one_or_none()
    if not lesson:
        raise NotFoundError("Lesson not found")
    module = (
        await db.execute(
            select(CourseModule).where(CourseModule.id == lesson.module_id)
        )
    ).scalar_one()

    enrollment = (
        await db.execute(
            select(CourseEnrollment)
            .where(CourseEnrollment.employee_id == employee.id)
            .where(CourseEnrollment.course_id == module.course_id)
        )
    ).scalar_one_or_none()
    if not enrollment:
        raise ValidationError(
            "You are not enrolled in this course; enrol first"
        )

    progress = (
        await db.execute(
            select(LessonProgress)
            .where(LessonProgress.enrollment_id == enrollment.id)
            .where(LessonProgress.lesson_id == lesson_id)
        )
    ).scalar_one_or_none()
    new_completion = progress is None or progress.status != "completed"

    if not progress:
        progress = LessonProgress(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            status="completed",
            time_spent_seconds=time_spent_seconds,
            completed_at=_now(),
            notes=notes,
        )
        db.add(progress)
    else:
        progress.status = "completed"
        progress.time_spent_seconds += time_spent_seconds
        progress.completed_at = _now()
        if notes:
            progress.notes = notes

    # Recompute enrollment progress
    all_lessons = await _all_lesson_ids_for_course(db, module.course_id)
    if all_lessons:
        completed_q = await db.execute(
            select(func.count(LessonProgress.id))
            .where(LessonProgress.enrollment_id == enrollment.id)
            .where(LessonProgress.status == "completed")
            .where(LessonProgress.lesson_id.in_(all_lessons))
        )
        completed_count = completed_q.scalar() or 0
        # Include the current one if newly added
        if not progress.id:
            completed_count += 1
        pct = int((completed_count / len(all_lessons)) * 100)
        enrollment.progress_percentage = min(100, pct)
        if pct >= 100:
            if enrollment.status != "completed":
                enrollment.status = "completed"
                enrollment.completed_at = _now()
        elif enrollment.status == "enrolled":
            enrollment.status = "in_progress"

    await db.commit()
    await db.refresh(progress)
    await db.refresh(enrollment)

    if new_completion:
        await _award_points_for_lesson(db, employee, lesson, enrollment)

    return progress


async def _award_points_for_lesson(
    db: AsyncSession,
    employee: Employee,
    lesson: CourseLesson,
    enrollment: CourseEnrollment,
) -> None:
    stat = await _get_or_create_stat(db, employee.id)
    stat.points += lesson.points
    stat.lessons_completed += 1

    # Update streak: consecutive activity days
    today = _today()
    if stat.last_activity_date is None:
        stat.streak_days = 1
    elif stat.last_activity_date == today:
        pass
    elif stat.last_activity_date == today - timedelta(days=1):
        stat.streak_days += 1
    else:
        stat.streak_days = 1
    stat.last_activity_date = today

    # Course completion bonus
    if enrollment.status == "completed" and enrollment.completed_at == _now() or (
        enrollment.status == "completed"
    ):
        course = (
            await db.execute(
                select(Course).where(Course.id == enrollment.course_id)
            )
        ).scalar_one()
        # Award only if not already counted (rough check by ensuring this lesson
        # completion drove progress to 100).
        if enrollment.progress_percentage == 100:
            # Avoid double-counting: count distinct completed enrollments.
            cnt = (
                await db.execute(
                    select(func.count(CourseEnrollment.id))
                    .where(CourseEnrollment.employee_id == employee.id)
                    .where(CourseEnrollment.status == "completed")
                )
            ).scalar() or 0
            if cnt > stat.courses_completed:
                stat.points += course.points
                stat.courses_completed = cnt

    stat.level = _level_for_points(stat.points)
    await db.commit()
    await _check_and_award_badges(db, employee, stat)


async def _get_or_create_stat(
    db: AsyncSession, employee_id: int
) -> EmployeeLearningStat:
    stat = (
        await db.execute(
            select(EmployeeLearningStat).where(
                EmployeeLearningStat.employee_id == employee_id
            )
        )
    ).scalar_one_or_none()
    if stat:
        return stat
    stat = EmployeeLearningStat(employee_id=employee_id)
    db.add(stat)
    await db.flush()
    return stat


async def _check_and_award_badges(
    db: AsyncSession,
    employee: Employee,
    stat: EmployeeLearningStat,
) -> None:
    badges = (await db.execute(select(Badge))).scalars().all()
    earned = (
        await db.execute(
            select(EmployeeBadge.badge_id).where(
                EmployeeBadge.employee_id == employee.id
            )
        )
    ).scalars().all()
    earned_set = set(earned)
    for badge in badges:
        if badge.id in earned_set:
            continue
        if (
            stat.points >= badge.points_required
            and stat.courses_completed >= badge.courses_required
            and stat.streak_days >= badge.streak_days_required
        ):
            db.add(
                EmployeeBadge(
                    employee_id=employee.id,
                    badge_id=badge.id,
                    awarded_at=_now(),
                )
            )
    await db.commit()


# ── Stats / leaderboard ─────────────────────────────────────────────
async def get_employee_stats(
    db: AsyncSession, employee_id: int
) -> dict:
    stat = await _get_or_create_stat(db, employee_id)
    badge_ids = (
        await db.execute(
            select(EmployeeBadge.badge_id).where(
                EmployeeBadge.employee_id == employee_id
            )
        )
    ).scalars().all()
    badges = []
    if badge_ids:
        badges = (
            await db.execute(select(Badge).where(Badge.id.in_(badge_ids)))
        ).scalars().all()
    return {
        "employee_id": stat.employee_id,
        "points": stat.points,
        "courses_completed": stat.courses_completed,
        "lessons_completed": stat.lessons_completed,
        "streak_days": stat.streak_days,
        "last_activity_date": stat.last_activity_date,
        "level": stat.level,
        "badges": badges,
    }


async def leaderboard(
    db: AsyncSession,
    *,
    department_id: Optional[int] = None,
    limit: int = 20,
) -> list[dict]:
    stmt = (
        select(EmployeeLearningStat, Employee)
        .join(Employee, Employee.id == EmployeeLearningStat.employee_id)
        .order_by(EmployeeLearningStat.points.desc())
        .limit(limit)
    )
    if department_id is not None:
        stmt = stmt.where(Employee.department_id == department_id)
    rows = (await db.execute(stmt)).all()
    return [
        {
            "employee_id": emp.id,
            "employee_code": emp.employee_code,
            "name": f"{emp.first_name} {emp.last_name}".strip(),
            "points": stat.points,
            "courses_completed": stat.courses_completed,
            "level": stat.level,
            "streak_days": stat.streak_days,
        }
        for stat, emp in rows
    ]


async def compliance_status(
    db: AsyncSession, employee_id: int
) -> list[dict]:
    """Lists every published mandatory course with the employee's status."""
    courses = await list_courses(
        db, mandatory_only=True, published_only=True, limit=500
    )
    enrollments = (
        await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.employee_id == employee_id
            )
        )
    ).scalars().all()
    by_course = {e.course_id: e for e in enrollments}
    out = []
    today = _today()
    for c in courses:
        e = by_course.get(c.id)
        next_due = None
        status = "not_enrolled"
        if e:
            status = e.status
            if (
                e.status == "completed"
                and c.validity_months
                and e.completed_at
            ):
                next_due = (
                    e.completed_at.date()
                    + timedelta(days=30 * c.validity_months)
                )
                if today > next_due:
                    status = "expired"
        out.append(
            {
                "course_id": c.id,
                "course_code": c.code,
                "title": c.title,
                "category": c.category,
                "status": status,
                "progress_percentage": e.progress_percentage if e else 0,
                "completed_at": e.completed_at if e else None,
                "next_due_at": next_due,
            }
        )
    return out


# ── Course mutations: update + delete ─────────────────────────────────
async def update_course(
    db: AsyncSession, course_id: int, *, payload: dict
) -> Course:
    course = await get_course(db, course_id)
    # Whitelist editable columns — we never want is_published flipped
    # silently here (use publish_course() for that).
    allowed = {
        "title", "description", "category", "department_id", "difficulty",
        "estimated_hours", "thumbnail_url", "is_mandatory",
        "validity_months", "points",
    }
    for k, v in payload.items():
        if k in allowed:
            setattr(course, k, v)
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course_id: int) -> None:
    course = await get_course(db, course_id)
    await db.delete(course)
    await db.commit()

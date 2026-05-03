from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.lms import (
    CourseCreate,
    CourseOut,
    CoursePublishUpdate,
    CourseSummary,
    CourseUpdate,
    EnrollmentCreate,
    EnrollmentOut,
    LeaderboardEntry,
    LearningStatsOut,
    LessonCompleteRequest,
    LessonCreate,
    LessonOut,
    ModuleCreate,
    ModuleOut,
)
from app.services import employee_service as emp_svc
from app.services import lms_service as lms_svc

router = APIRouter(prefix="/lms", tags=["lms"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ─── Courses (catalog) ────────────────────────────────────────────────
@router.get("/courses", response_model=list[CourseSummary])
async def list_courses(
    category: Optional[str] = None,
    department_id: Optional[int] = None,
    include_unpublished: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Employees see only published courses. Admins / HR can opt in to
    unpublished + drafts via include_unpublished=true."""
    show_drafts = False
    if include_unpublished:
        from app.core.permissions import Role as RoleEnum
        if set(user.role_codes) & {
            RoleEnum.SUPER_ADMIN.value,
            RoleEnum.HR.value,
            RoleEnum.ADMIN.value,
            RoleEnum.DIRECTOR.value,
        }:
            show_drafts = True
    return await lms_svc.list_courses(
        db,
        category=category,
        department_id=department_id,
        published_only=not show_drafts,
    )


@router.get("/courses/mandatory", response_model=list[CourseSummary])
async def mandatory_courses(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await lms_svc.list_courses(db, mandatory_only=True)


@router.get("/courses/{course_id}", response_model=CourseOut)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await lms_svc.get_course(db, course_id)


@router.post(
    "/courses",
    response_model=CourseOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("admin.users.manage")),
):
    return await lms_svc.create_course(
        db, payload=payload.model_dump(), created_by=user.id
    )


@router.post("/courses/{course_id}/publish", response_model=CourseOut)
async def publish_course(
    course_id: int,
    payload: CoursePublishUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await lms_svc.publish_course(
        db, course_id, is_published=payload.is_published
    )


@router.put("/courses/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await lms_svc.update_course(
        db, course_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    await lms_svc.delete_course(db, course_id)


@router.post(
    "/courses/{course_id}/modules",
    response_model=ModuleOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_module(
    course_id: int,
    payload: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await lms_svc.add_module(
        db, course_id, payload=payload.model_dump()
    )


@router.post(
    "/modules/{module_id}/lessons",
    response_model=LessonOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_lesson(
    module_id: int,
    payload: LessonCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await lms_svc.add_lesson(db, module_id, payload=payload.model_dump())


# ─── Enrollment ───────────────────────────────────────────────────────
@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def enroll(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await lms_svc.enroll(db, course_id=course_id, employee=emp)


@router.post(
    "/enroll",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_enroll(
    payload: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    """Admin-side: assign a course to an employee with optional due date."""
    from app.models import Employee
    from sqlalchemy import select

    if payload.employee_id is None:
        raise NotFoundError("employee_id required for admin enrollment")
    emp = (
        await db.execute(
            select(Employee).where(Employee.id == payload.employee_id)
        )
    ).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")
    return await lms_svc.enroll(
        db,
        course_id=payload.course_id,
        employee=emp,
        due_date=payload.due_date,
    )


@router.get("/my-courses", response_model=list[EnrollmentOut])
async def my_courses(
    enrollment_status: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await lms_svc.list_my_enrollments(
        db, emp.id, status=enrollment_status
    )


@router.post("/lessons/{lesson_id}/complete", response_model=EnrollmentOut)
async def complete_lesson(
    lesson_id: int,
    payload: LessonCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    progress = await lms_svc.complete_lesson(
        db,
        employee=emp,
        lesson_id=lesson_id,
        time_spent_seconds=payload.time_spent_seconds,
        notes=payload.notes,
    )
    enrollment = await lms_svc.get_enrollment(db, progress.enrollment_id)
    return enrollment


# ─── Compliance / stats / leaderboard ─────────────────────────────────
@router.get("/compliance/me")
async def my_compliance(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await lms_svc.compliance_status(db, emp.id)


@router.get("/stats/me", response_model=LearningStatsOut)
async def my_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await lms_svc.get_employee_stats(db, emp.id)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    department_id: Optional[int] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await lms_svc.leaderboard(
        db, department_id=department_id, limit=limit
    )

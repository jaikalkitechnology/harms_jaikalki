from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Employee, FeedbackRequest, User
from app.schemas.performance import (
    FeedbackAggregate,
    FeedbackRequestCreate,
    FeedbackRequestOut,
    FeedbackResponseOut,
    FeedbackResponseSubmit,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    OneOnOneCreate,
    OneOnOneOut,
    ReviewOut,
    ReviewSubmit,
)
from app.services import employee_service as emp_svc
from app.services import performance_service as perf

router = APIRouter(prefix="/performance", tags=["performance"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# Cycle management is no longer exposed via the public API. The
# ReviewCycle model still exists internally because goals / reviews /
# reports reference it, but admins / mobile no longer manage cycles
# through HTTP endpoints. Cycles are now considered an internal
# implementation detail of the review pipeline.


# ─── Goals ───────────────────────────────────────────────────────────
@router.get("/goals/me", response_model=list[GoalOut])
async def my_goals(
    cycle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await perf.list_goals(db, employee_id=emp.id, cycle_id=cycle_id)


@router.post(
    "/goals",
    response_model=GoalOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_goal(
    payload: GoalCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    data = payload.model_dump()
    target = data.get("employee_id")
    # If a target other than self is given, only managers/HR can create
    if target and target != emp.id:
        if not (
            set(user.role_codes)
            & {"super_admin", "director", "hr", "admin", "manager"}
        ):
            raise ForbiddenError("Only managers/HR can assign goals to others")
    return await perf.create_goal(
        db, payload=data, employee=emp, creator_user_id=user.id
    )


@router.patch("/goals/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    g = await perf.get_goal(db, goal_id)
    emp = await _self_employee(db, user)
    if g.employee_id != emp.id:
        if not (
            set(user.role_codes)
            & {"super_admin", "director", "hr", "admin", "manager"}
        ):
            raise ForbiddenError("Not your goal")
    return await perf.update_goal(
        db, goal_id, payload=payload.model_dump(exclude_unset=True)
    )


# ─── Reviews ─────────────────────────────────────────────────────────
@router.post(
    "/cycles/{cycle_id}/self-review", response_model=ReviewOut
)
async def submit_self_review(
    cycle_id: int,
    payload: ReviewSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cycle = await perf.get_cycle(db, cycle_id)
    emp = await _self_employee(db, user)
    return await perf.submit_self_review(
        db, cycle=cycle, employee=emp, user=user, payload=payload.model_dump()
    )


@router.post(
    "/cycles/{cycle_id}/manager-review/{employee_id}",
    response_model=ReviewOut,
)
async def submit_manager_review(
    cycle_id: int,
    employee_id: int,
    payload: ReviewSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cycle = await perf.get_cycle(db, cycle_id)
    subject = (
        await db.execute(select(Employee).where(Employee.id == employee_id))
    ).scalar_one_or_none()
    if not subject:
        raise NotFoundError("Employee not found")
    manager_emp = await _self_employee(db, user)
    return await perf.submit_manager_review(
        db,
        cycle=cycle,
        subject_employee=subject,
        manager_user=user,
        manager_employee=manager_emp,
        payload=payload.model_dump(),
    )


@router.post("/reviews/{review_id}/share", response_model=ReviewOut)
async def share_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await perf.share_review(db, review_id)


@router.post("/reviews/{review_id}/acknowledge", response_model=ReviewOut)
async def acknowledge_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await perf.acknowledge_review(db, review_id, employee=emp)


@router.get("/reviews/me", response_model=list[ReviewOut])
async def my_reviews(
    cycle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await perf.list_reviews_for_employee(
        db, employee_id=emp.id, cycle_id=cycle_id
    )


# ─── 360 Feedback ────────────────────────────────────────────────────
@router.post(
    "/feedback/requests",
    response_model=list[FeedbackRequestOut],
    status_code=status.HTTP_201_CREATED,
)
async def request_feedback(
    payload: FeedbackRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await perf.request_feedback(
        db,
        cycle_id=payload.cycle_id,
        subject_employee_id=payload.subject_employee_id,
        reviewer_employee_ids=payload.reviewer_employee_ids,
        relation=payload.relation,
        is_anonymous=payload.is_anonymous,
        requested_by_user_id=user.id,
    )


@router.get("/feedback/me/pending", response_model=list[FeedbackRequestOut])
async def my_pending_feedback(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await perf.my_pending_feedback(db, reviewer_employee_id=emp.id)


@router.post(
    "/feedback/requests/{request_id}/respond",
    response_model=FeedbackResponseOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    request_id: int,
    payload: FeedbackResponseSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    req = (
        await db.execute(
            select(FeedbackRequest).where(FeedbackRequest.id == request_id)
        )
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("Feedback request not found")
    emp = await _self_employee(db, user)
    return await perf.submit_feedback(
        db, request=req, reviewer=emp, payload=payload.model_dump()
    )


@router.get(
    "/feedback/aggregate/{employee_id}",
    response_model=FeedbackAggregate,
)
async def aggregate_feedback(
    employee_id: int,
    cycle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Subject themselves or HR/manager can view
    emp = await _self_employee(db, user)
    if emp.id != employee_id and not (
        set(user.role_codes)
        & {"super_admin", "director", "hr", "admin", "manager"}
    ):
        raise ForbiddenError("Not allowed")
    return await perf.aggregate_feedback(
        db, subject_employee_id=employee_id, cycle_id=cycle_id
    )


# ─── 1-on-1 ──────────────────────────────────────────────────────────
@router.post(
    "/one-on-one",
    response_model=OneOnOneOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_one_on_one(
    payload: OneOnOneCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    manager_emp = await _self_employee(db, user)
    return await perf.create_one_on_one(
        db,
        manager_user=user,
        manager_employee=manager_emp,
        payload=payload.model_dump(),
    )


@router.get("/one-on-one/me", response_model=list[OneOnOneOut])
async def my_one_on_ones(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await perf.list_one_on_ones_for_employee(db, employee_id=emp.id)


@router.get(
    "/one-on-one/team", response_model=list[OneOnOneOut]
)
async def my_team_one_on_ones(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await perf.list_one_on_ones_for_manager(db, manager_id=emp.id)

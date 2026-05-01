"""Performance management: cycles, goals, reviews, 360, 1-on-1s."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Employee,
    FeedbackRequest,
    FeedbackResponse,
    Goal,
    OneOnOneNote,
    PerformanceReview,
    ReviewCycle,
    User,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    return _now().date()


# ── Cycles ──────────────────────────────────────────────────────────
async def create_cycle(
    db: AsyncSession, *, payload: dict
) -> ReviewCycle:
    if payload["period_end"] <= payload["period_start"]:
        raise ValidationError("period_end must be after period_start")
    if (
        await db.execute(
            select(ReviewCycle).where(ReviewCycle.code == payload["code"])
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Cycle code '{payload['code']}' exists")
    cycle = ReviewCycle(**payload, status="draft")
    db.add(cycle)
    await db.commit()
    await db.refresh(cycle)
    return cycle


async def list_cycles(
    db: AsyncSession, *, status: Optional[str] = None
) -> Sequence[ReviewCycle]:
    stmt = select(ReviewCycle)
    if status:
        stmt = stmt.where(ReviewCycle.status == status)
    stmt = stmt.order_by(ReviewCycle.period_start.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_cycle(db: AsyncSession, cycle_id: int) -> ReviewCycle:
    c = (
        await db.execute(
            select(ReviewCycle).where(ReviewCycle.id == cycle_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise NotFoundError("Cycle not found")
    return c


async def update_cycle_status(
    db: AsyncSession, cycle_id: int, *, status: str
) -> ReviewCycle:
    c = await get_cycle(db, cycle_id)
    c.status = status
    await db.commit()
    await db.refresh(c)
    return c


# ── Goals ───────────────────────────────────────────────────────────
async def create_goal(
    db: AsyncSession,
    *,
    payload: dict,
    employee: Employee,
    creator_user_id: Optional[int] = None,
) -> Goal:
    target_emp_id = payload.pop("employee_id", None) or employee.id
    if payload.get("cycle_id"):
        await get_cycle(db, payload["cycle_id"])
    goal = Goal(
        employee_id=target_emp_id,
        created_by=creator_user_id,
        status="active",
        **payload,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def list_goals(
    db: AsyncSession,
    *,
    employee_id: int,
    cycle_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Sequence[Goal]:
    stmt = select(Goal).where(Goal.employee_id == employee_id)
    if cycle_id is not None:
        stmt = stmt.where(Goal.cycle_id == cycle_id)
    if status:
        stmt = stmt.where(Goal.status == status)
    stmt = stmt.order_by(Goal.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_goal(db: AsyncSession, goal_id: int) -> Goal:
    g = (
        await db.execute(select(Goal).where(Goal.id == goal_id))
    ).scalar_one_or_none()
    if not g:
        raise NotFoundError("Goal not found")
    return g


async def update_goal(
    db: AsyncSession, goal_id: int, *, payload: dict
) -> Goal:
    g = await get_goal(db, goal_id)
    for key, value in payload.items():
        if value is not None:
            setattr(g, key, value)
    if g.progress_pct is not None and g.progress_pct >= 100 and g.status not in (
        "achieved",
        "missed",
        "cancelled",
    ):
        g.status = "achieved"
    await db.commit()
    await db.refresh(g)
    return g


# ── Reviews ─────────────────────────────────────────────────────────
async def _ensure_review(
    db: AsyncSession,
    *,
    cycle_id: int,
    employee_id: int,
    review_type: str,
    reviewer_id: Optional[int],
) -> PerformanceReview:
    review = (
        await db.execute(
            select(PerformanceReview)
            .where(PerformanceReview.cycle_id == cycle_id)
            .where(PerformanceReview.employee_id == employee_id)
            .where(PerformanceReview.review_type == review_type)
        )
    ).scalar_one_or_none()
    if review:
        return review
    review = PerformanceReview(
        cycle_id=cycle_id,
        employee_id=employee_id,
        review_type=review_type,
        reviewer_id=reviewer_id,
        status="draft",
    )
    db.add(review)
    await db.flush()
    return review


async def submit_self_review(
    db: AsyncSession,
    *,
    cycle: ReviewCycle,
    employee: Employee,
    user: User,
    payload: dict,
) -> PerformanceReview:
    if cycle.status not in ("open", "review"):
        raise ValidationError("Cycle is not open for self review")
    review = await _ensure_review(
        db,
        cycle_id=cycle.id,
        employee_id=employee.id,
        review_type="self",
        reviewer_id=user.id,
    )
    if review.status not in ("draft", "submitted"):
        raise ValidationError(f"Self review already {review.status}")
    for key, value in payload.items():
        if value is not None:
            setattr(review, key, value)
    review.status = "submitted"
    review.submitted_at = _now()
    review.reviewer_id = user.id
    await db.commit()
    await db.refresh(review)
    return review


async def submit_manager_review(
    db: AsyncSession,
    *,
    cycle: ReviewCycle,
    subject_employee: Employee,
    manager_user: User,
    manager_employee: Employee,
    payload: dict,
    review_type: str = "manager",
) -> PerformanceReview:
    if cycle.status not in ("open", "review"):
        raise ValidationError("Cycle is not open for reviews")
    if review_type == "manager":
        if subject_employee.reporting_to != manager_employee.id:
            raise ForbiddenError(
                "You are not the direct manager of this employee"
            )
    review = await _ensure_review(
        db,
        cycle_id=cycle.id,
        employee_id=subject_employee.id,
        review_type=review_type,
        reviewer_id=manager_user.id,
    )
    if review.status not in ("draft", "submitted"):
        raise ValidationError(f"Review already {review.status}")
    for key, value in payload.items():
        if value is not None:
            setattr(review, key, value)
    review.status = "submitted"
    review.submitted_at = _now()
    review.reviewer_id = manager_user.id
    await db.commit()
    await db.refresh(review)
    return review


async def list_reviews_for_employee(
    db: AsyncSession,
    *,
    employee_id: int,
    cycle_id: Optional[int] = None,
) -> Sequence[PerformanceReview]:
    stmt = select(PerformanceReview).where(
        PerformanceReview.employee_id == employee_id
    )
    if cycle_id is not None:
        stmt = stmt.where(PerformanceReview.cycle_id == cycle_id)
    stmt = stmt.order_by(PerformanceReview.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def acknowledge_review(
    db: AsyncSession,
    review_id: int,
    *,
    employee: Employee,
) -> PerformanceReview:
    review = (
        await db.execute(
            select(PerformanceReview).where(PerformanceReview.id == review_id)
        )
    ).scalar_one_or_none()
    if not review:
        raise NotFoundError("Review not found")
    if review.employee_id != employee.id:
        raise ForbiddenError("Not your review")
    if review.status != "shared_with_employee":
        raise ValidationError(
            "Review must be shared before it can be acknowledged"
        )
    review.status = "acknowledged"
    review.acknowledged_at = _now()
    await db.commit()
    await db.refresh(review)
    return review


async def share_review(
    db: AsyncSession, review_id: int
) -> PerformanceReview:
    review = (
        await db.execute(
            select(PerformanceReview).where(PerformanceReview.id == review_id)
        )
    ).scalar_one_or_none()
    if not review:
        raise NotFoundError("Review not found")
    if review.status not in ("submitted", "calibrated"):
        raise ValidationError(
            "Only submitted or calibrated reviews can be shared"
        )
    review.status = "shared_with_employee"
    await db.commit()
    await db.refresh(review)
    return review


# ── 360 Feedback ────────────────────────────────────────────────────
async def request_feedback(
    db: AsyncSession,
    *,
    cycle_id: Optional[int],
    subject_employee_id: int,
    reviewer_employee_ids: list[int],
    relation: str,
    is_anonymous: bool,
    requested_by_user_id: int,
) -> list[FeedbackRequest]:
    if cycle_id is not None:
        await get_cycle(db, cycle_id)
    out = []
    for rid in reviewer_employee_ids:
        if rid == subject_employee_id:
            continue
        existing = (
            await db.execute(
                select(FeedbackRequest)
                .where(FeedbackRequest.cycle_id == cycle_id)
                .where(
                    FeedbackRequest.subject_employee_id == subject_employee_id
                )
                .where(FeedbackRequest.reviewer_employee_id == rid)
            )
        ).scalar_one_or_none()
        if existing:
            out.append(existing)
            continue
        req = FeedbackRequest(
            cycle_id=cycle_id,
            subject_employee_id=subject_employee_id,
            reviewer_employee_id=rid,
            relation=relation,
            is_anonymous=is_anonymous,
            status="pending",
            requested_by=requested_by_user_id,
        )
        db.add(req)
        out.append(req)
    await db.commit()
    for r in out:
        await db.refresh(r)
    return out


async def my_pending_feedback(
    db: AsyncSession, *, reviewer_employee_id: int
) -> Sequence[FeedbackRequest]:
    return (
        await db.execute(
            select(FeedbackRequest)
            .where(FeedbackRequest.reviewer_employee_id == reviewer_employee_id)
            .where(FeedbackRequest.status == "pending")
            .order_by(FeedbackRequest.created_at.desc())
        )
    ).scalars().all()


async def submit_feedback(
    db: AsyncSession,
    *,
    request: FeedbackRequest,
    reviewer: Employee,
    payload: dict,
) -> FeedbackResponse:
    if request.reviewer_employee_id != reviewer.id:
        raise ForbiddenError("Not your feedback request")
    if request.status != "pending":
        raise ValidationError(f"Request already {request.status}")
    response = FeedbackResponse(
        request_id=request.id,
        overall_rating=payload.get("overall_rating"),
        strengths=payload.get("strengths"),
        improvement_areas=payload.get("improvement_areas"),
        competencies=payload.get("competencies"),
        submitted_at=_now(),
    )
    db.add(response)
    request.status = "submitted"
    await db.commit()
    await db.refresh(response)
    return response


async def aggregate_feedback(
    db: AsyncSession, *, subject_employee_id: int, cycle_id: Optional[int] = None
) -> dict:
    stmt = (
        select(FeedbackRequest, FeedbackResponse)
        .join(
            FeedbackResponse,
            FeedbackResponse.request_id == FeedbackRequest.id,
        )
        .where(FeedbackRequest.subject_employee_id == subject_employee_id)
    )
    if cycle_id is not None:
        stmt = stmt.where(FeedbackRequest.cycle_id == cycle_id)
    rows = (await db.execute(stmt)).all()

    if not rows:
        return {
            "subject_employee_id": subject_employee_id,
            "response_count": 0,
            "avg_rating": 0.0,
            "competency_averages": {},
            "anonymous_strengths": [],
            "anonymous_improvements": [],
        }

    ratings = []
    competency_sums: dict[str, list[float]] = {}
    strengths = []
    improvements = []
    for req, resp in rows:
        if resp.overall_rating is not None:
            ratings.append(float(resp.overall_rating))
        if resp.competencies:
            for k, v in resp.competencies.items():
                try:
                    competency_sums.setdefault(k, []).append(float(v))
                except (TypeError, ValueError):
                    continue
        # Always anonymise the comments in aggregate output
        if resp.strengths:
            strengths.append(resp.strengths)
        if resp.improvement_areas:
            improvements.append(resp.improvement_areas)
    return {
        "subject_employee_id": subject_employee_id,
        "response_count": len(rows),
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0.0,
        "competency_averages": {
            k: round(sum(v) / len(v), 2) for k, v in competency_sums.items()
        },
        "anonymous_strengths": strengths,
        "anonymous_improvements": improvements,
    }


# ── 1-on-1 ──────────────────────────────────────────────────────────
async def create_one_on_one(
    db: AsyncSession,
    *,
    manager_user: User,
    manager_employee: Employee,
    payload: dict,
) -> OneOnOneNote:
    employee_id = payload.pop("employee_id")
    subject = (
        await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
    ).scalar_one_or_none()
    if not subject:
        raise NotFoundError("Employee not found")
    if subject.reporting_to != manager_employee.id:
        raise ForbiddenError(
            "You can only log 1-on-1s with your direct reportees"
        )

    note = OneOnOneNote(
        employee_id=subject.id,
        manager_id=manager_employee.id,
        created_by=manager_user.id,
        **payload,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def list_one_on_ones_for_pair(
    db: AsyncSession, *, employee_id: int, manager_id: int
) -> Sequence[OneOnOneNote]:
    return (
        await db.execute(
            select(OneOnOneNote)
            .where(OneOnOneNote.employee_id == employee_id)
            .where(OneOnOneNote.manager_id == manager_id)
            .order_by(OneOnOneNote.meeting_date.desc())
        )
    ).scalars().all()


async def list_one_on_ones_for_employee(
    db: AsyncSession, *, employee_id: int
) -> Sequence[OneOnOneNote]:
    """List 1-on-1s the employee can see — only the 'shared' ones."""
    return (
        await db.execute(
            select(OneOnOneNote)
            .where(OneOnOneNote.employee_id == employee_id)
            .where(OneOnOneNote.visibility == "shared")
            .order_by(OneOnOneNote.meeting_date.desc())
        )
    ).scalars().all()


async def list_one_on_ones_for_manager(
    db: AsyncSession, *, manager_id: int
) -> Sequence[OneOnOneNote]:
    return (
        await db.execute(
            select(OneOnOneNote)
            .where(OneOnOneNote.manager_id == manager_id)
            .order_by(OneOnOneNote.meeting_date.desc())
        )
    ).scalars().all()

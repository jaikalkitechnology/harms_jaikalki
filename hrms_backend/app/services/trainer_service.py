"""Trainer service: profiles, sessions, QR check-in, reviews, analytics."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
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
    SessionParticipant,
    TrainerProfile,
    TrainerReview,
    TrainingSession,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Trainer profile ──────────────────────────────────────────────────
async def create_trainer(
    db: AsyncSession, *, payload: dict
) -> TrainerProfile:
    if payload.get("employee_id"):
        existing = (
            await db.execute(
                select(TrainerProfile).where(
                    TrainerProfile.employee_id == payload["employee_id"]
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(
                "Employee already has a trainer profile"
            )
    if not payload.get("is_external") and not payload.get("employee_id"):
        raise ValidationError(
            "Internal trainers must reference an existing employee_id"
        )

    profile = TrainerProfile(**payload, is_active=True)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def list_trainers(
    db: AsyncSession,
    *,
    specialization: Optional[str] = None,
    is_external: Optional[bool] = None,
    search: Optional[str] = None,
    active_only: bool = True,
) -> Sequence[TrainerProfile]:
    stmt = select(TrainerProfile)
    if active_only:
        stmt = stmt.where(TrainerProfile.is_active.is_(True))
    if is_external is not None:
        stmt = stmt.where(TrainerProfile.is_external.is_(is_external))
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                TrainerProfile.full_name.ilike(like),
                TrainerProfile.headline.ilike(like),
                TrainerProfile.bio.ilike(like),
                TrainerProfile.contact_email.ilike(like),
            )
        )
    stmt = stmt.order_by(
        TrainerProfile.rating_average.desc(),
        TrainerProfile.sessions_completed.desc(),
    )
    rows = (await db.execute(stmt)).scalars().all()
    if specialization:
        rows = [
            r
            for r in rows
            if r.specializations and specialization in r.specializations
        ]
    return rows


async def get_trainer(
    db: AsyncSession, trainer_id: int
) -> TrainerProfile:
    t = (
        await db.execute(
            select(TrainerProfile).where(TrainerProfile.id == trainer_id)
        )
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Trainer not found")
    return t


async def update_trainer(
    db: AsyncSession, trainer_id: int, *, payload: dict
) -> TrainerProfile:
    t = await get_trainer(db, trainer_id)
    allowed = {
        "full_name", "headline", "bio", "contact_email", "contact_phone",
        "profile_photo_url", "languages", "specializations",
        "years_experience", "hourly_rate", "is_active",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return t


async def delete_trainer(db: AsyncSession, trainer_id: int) -> None:
    """Soft-delete: mark inactive so existing sessions stay valid."""
    t = await get_trainer(db, trainer_id)
    t.is_active = False
    await db.commit()


# ── Training sessions ───────────────────────────────────────────────
def _sessions_overlap(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> bool:
    return a_start < b_end and b_start < a_end


async def schedule_session(
    db: AsyncSession, *, payload: dict
) -> TrainingSession:
    if payload["scheduled_end"] <= payload["scheduled_start"]:
        raise ValidationError("scheduled_end must be after scheduled_start")
    trainer = await get_trainer(db, payload["trainer_id"])
    if not trainer.is_active:
        raise ValidationError("Trainer is inactive")

    if (
        await db.execute(
            select(TrainingSession).where(
                TrainingSession.code == payload["code"]
            )
        )
    ).scalar_one_or_none():
        raise ConflictError(f"Session code '{payload['code']}' already exists")

    # Conflict check against trainer's other sessions
    overlap = (
        await db.execute(
            select(TrainingSession)
            .where(TrainingSession.trainer_id == trainer.id)
            .where(TrainingSession.status != "cancelled")
            .where(
                TrainingSession.scheduled_start < payload["scheduled_end"]
            )
            .where(
                TrainingSession.scheduled_end > payload["scheduled_start"]
            )
        )
    ).scalars().all()
    if overlap:
        raise ConflictError(
            f"Trainer already has {len(overlap)} session(s) in this time slot"
        )

    session = TrainingSession(
        **payload,
        qr_token=secrets.token_urlsafe(16),
        status="open_for_registration",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(
    db: AsyncSession,
    *,
    trainer_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    upcoming_only: bool = False,
    search: Optional[str] = None,
) -> Sequence[TrainingSession]:
    stmt = select(TrainingSession)
    if trainer_id is not None:
        stmt = stmt.where(TrainingSession.trainer_id == trainer_id)
    if status:
        stmt = stmt.where(TrainingSession.status == status)
    if upcoming_only:
        stmt = stmt.where(TrainingSession.scheduled_end >= _now())
    if employee_id is not None:
        sub = select(SessionParticipant.session_id).where(
            SessionParticipant.employee_id == employee_id
        )
        stmt = stmt.where(TrainingSession.id.in_(sub))
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                TrainingSession.code.ilike(like),
                TrainingSession.title.ilike(like),
                TrainingSession.description.ilike(like),
                TrainingSession.location.ilike(like),
            )
        )
    stmt = stmt.order_by(TrainingSession.scheduled_start.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_session(
    db: AsyncSession, session_id: int
) -> TrainingSession:
    s = (
        await db.execute(
            select(TrainingSession).where(TrainingSession.id == session_id)
        )
    ).scalar_one_or_none()
    if not s:
        raise NotFoundError("Session not found")
    return s


async def update_session(
    db: AsyncSession, session_id: int, *, payload: dict
) -> TrainingSession:
    s = await get_session(db, session_id)
    if s.status in ("completed", "cancelled"):
        raise ValidationError(
            f"Cannot edit a {s.status} session"
        )
    allowed = {
        "title", "description", "trainer_id", "course_id", "department_id",
        "session_type", "scheduled_start", "scheduled_end", "timezone",
        "location", "meeting_url", "capacity",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


async def update_session_status(
    db: AsyncSession, session_id: int, *, status: str
) -> TrainingSession:
    s = await get_session(db, session_id)
    s.status = status
    if status == "completed":
        # Mark attended participants as completed
        for p in s.participants:
            if p.status == "attended":
                p.status = "completed"
                p.completed_at = _now()
            elif p.status == "registered":
                p.status = "no_show"
        # Roll up trainer stats
        trainer = await get_trainer(db, s.trainer_id)
        trainer.sessions_completed += 1
    await db.commit()
    await db.refresh(s)
    return s


# ── Registration & QR check-in ──────────────────────────────────────
async def register_participant(
    db: AsyncSession, *, session: TrainingSession, employee: Employee
) -> SessionParticipant:
    if session.status not in ("open_for_registration", "scheduled"):
        raise ValidationError(
            f"Cannot register for a session in '{session.status}' status"
        )
    existing = (
        await db.execute(
            select(SessionParticipant)
            .where(SessionParticipant.session_id == session.id)
            .where(SessionParticipant.employee_id == employee.id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    count = (
        await db.execute(
            select(func.count(SessionParticipant.id)).where(
                SessionParticipant.session_id == session.id
            )
        )
    ).scalar() or 0
    if count >= session.capacity:
        raise ValidationError("Session is full")

    p = SessionParticipant(
        session_id=session.id,
        employee_id=employee.id,
        registered_at=_now(),
        status="registered",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def check_in_with_qr(
    db: AsyncSession,
    *,
    qr_token: str,
    employee: Employee,
) -> SessionParticipant:
    session = (
        await db.execute(
            select(TrainingSession).where(TrainingSession.qr_token == qr_token)
        )
    ).scalar_one_or_none()
    if not session:
        raise NotFoundError("Invalid QR code")
    if session.status not in ("in_progress", "open_for_registration", "scheduled"):
        raise ValidationError(
            f"Cannot check in to a {session.status} session"
        )

    p = (
        await db.execute(
            select(SessionParticipant)
            .where(SessionParticipant.session_id == session.id)
            .where(SessionParticipant.employee_id == employee.id)
        )
    ).scalar_one_or_none()
    if not p:
        # Auto-register if capacity allows
        p = await register_participant(db, session=session, employee=employee)
    if p.checked_in_at:
        return p
    p.checked_in_at = _now()
    p.status = "attended"
    if session.status != "in_progress":
        session.status = "in_progress"
    await db.commit()
    await db.refresh(p)
    return p


# ── Reviews ─────────────────────────────────────────────────────────
async def submit_review(
    db: AsyncSession,
    *,
    session: TrainingSession,
    employee: Employee,
    payload: dict,
) -> TrainerReview:
    if session.status != "completed":
        raise ValidationError("Can only review completed sessions")
    p = (
        await db.execute(
            select(SessionParticipant)
            .where(SessionParticipant.session_id == session.id)
            .where(SessionParticipant.employee_id == employee.id)
        )
    ).scalar_one_or_none()
    if not p or p.status not in ("attended", "completed"):
        raise ForbiddenError(
            "Only employees who attended this session can review it"
        )

    existing = (
        await db.execute(
            select(TrainerReview)
            .where(TrainerReview.session_id == session.id)
            .where(TrainerReview.employee_id == employee.id)
        )
    ).scalar_one_or_none()
    if existing:
        existing.rating = payload["rating"]
        existing.review_text = payload.get("review_text")
        existing.is_anonymous = payload.get("is_anonymous", False)
        review = existing
    else:
        review = TrainerReview(
            trainer_id=session.trainer_id,
            session_id=session.id,
            employee_id=employee.id,
            rating=payload["rating"],
            review_text=payload.get("review_text"),
            is_anonymous=payload.get("is_anonymous", False),
        )
        db.add(review)

    # Recompute trainer's rating average
    avg_q = await db.execute(
        select(func.avg(TrainerReview.rating)).where(
            TrainerReview.trainer_id == session.trainer_id
        )
    )
    avg_val = avg_q.scalar()
    trainer = await get_trainer(db, session.trainer_id)
    trainer.rating_average = (
        Decimal(str(round(float(avg_val), 2))) if avg_val else Decimal("0")
    )

    await db.commit()
    await db.refresh(review)
    return review


async def list_trainer_reviews(
    db: AsyncSession, trainer_id: int
) -> Sequence[TrainerReview]:
    return (
        await db.execute(
            select(TrainerReview)
            .where(TrainerReview.trainer_id == trainer_id)
            .order_by(TrainerReview.created_at.desc())
        )
    ).scalars().all()


# ── Analytics ───────────────────────────────────────────────────────
async def trainer_analytics(
    db: AsyncSession, trainer_id: int
) -> dict:
    trainer = await get_trainer(db, trainer_id)
    sessions = (
        await db.execute(
            select(TrainingSession).where(
                TrainingSession.trainer_id == trainer.id
            )
        )
    ).scalars().all()
    completed = [s for s in sessions if s.status == "completed"]
    upcoming = [
        s
        for s in sessions
        if s.scheduled_start >= _now() and s.status != "cancelled"
    ]

    participants_q = await db.execute(
        select(func.count(SessionParticipant.id))
        .join(
            TrainingSession,
            TrainingSession.id == SessionParticipant.session_id,
        )
        .where(TrainingSession.trainer_id == trainer.id)
    )
    total_participants = participants_q.scalar() or 0

    attended_q = await db.execute(
        select(func.count(SessionParticipant.id))
        .join(
            TrainingSession,
            TrainingSession.id == SessionParticipant.session_id,
        )
        .where(TrainingSession.trainer_id == trainer.id)
        .where(
            SessionParticipant.status.in_(["attended", "completed"])
        )
    )
    attended = attended_q.scalar() or 0

    review_count_q = await db.execute(
        select(func.count(TrainerReview.id)).where(
            TrainerReview.trainer_id == trainer.id
        )
    )
    review_count = review_count_q.scalar() or 0

    attendance_rate = (
        round((attended / total_participants) * 100, 2)
        if total_participants
        else 0.0
    )

    return {
        "trainer_id": trainer.id,
        "full_name": trainer.full_name,
        "sessions_completed": len(completed),
        "upcoming_sessions": len(upcoming),
        "total_participants": total_participants,
        "avg_rating": float(trainer.rating_average or 0),
        "review_count": review_count,
        "attendance_rate": attendance_rate,
    }

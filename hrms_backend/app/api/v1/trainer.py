from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.trainer import (
    CheckInRequest,
    ParticipantOut,
    ReviewCreate,
    ReviewOut,
    TrainerAnalytics,
    TrainerProfileCreate,
    TrainerProfileOut,
    TrainerProfileUpdate,
    TrainingSessionCreate,
    TrainingSessionOut,
    TrainingSessionStatusUpdate,
    TrainingSessionUpdate,
)
from app.services import employee_service as emp_svc
from app.services import trainer_service as t_svc

router = APIRouter(prefix="/trainer", tags=["trainer"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


def _session_to_out(session) -> TrainingSessionOut:
    out = TrainingSessionOut.model_validate(session)
    out.participants_count = len(session.participants or [])
    return out


# ─── Trainers ────────────────────────────────────────────────────────
@router.get("/trainers", response_model=list[TrainerProfileOut])
async def list_trainers(
    specialization: Optional[str] = None,
    is_external: Optional[bool] = None,
    search: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await t_svc.list_trainers(
        db,
        specialization=specialization,
        is_external=is_external,
        search=search,
        active_only=not include_inactive,
    )


@router.post(
    "/trainers",
    response_model=TrainerProfileOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_trainer(
    payload: TrainerProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await t_svc.create_trainer(db, payload=payload.model_dump())


@router.get("/trainers/{trainer_id}", response_model=TrainerProfileOut)
async def get_trainer(
    trainer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await t_svc.get_trainer(db, trainer_id)


@router.put("/trainers/{trainer_id}", response_model=TrainerProfileOut)
async def update_trainer(
    trainer_id: int,
    payload: TrainerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await t_svc.update_trainer(
        db, trainer_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/trainers/{trainer_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_trainer(
    trainer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    await t_svc.delete_trainer(db, trainer_id)


@router.get(
    "/trainers/{trainer_id}/analytics", response_model=TrainerAnalytics
)
async def trainer_analytics(
    trainer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await t_svc.trainer_analytics(db, trainer_id)


@router.get(
    "/trainers/{trainer_id}/reviews", response_model=list[ReviewOut]
)
async def trainer_reviews(
    trainer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await t_svc.list_trainer_reviews(db, trainer_id)


# ─── Sessions ────────────────────────────────────────────────────────
@router.get("/sessions", response_model=list[TrainingSessionOut])
async def list_sessions(
    trainer_id: Optional[int] = None,
    upcoming_only: bool = False,
    session_status: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    sessions = await t_svc.list_sessions(
        db,
        trainer_id=trainer_id,
        upcoming_only=upcoming_only,
        status=session_status,
        search=search,
    )
    return [_session_to_out(s) for s in sessions]


@router.put("/sessions/{session_id}", response_model=TrainingSessionOut)
async def update_session(
    session_id: int,
    payload: TrainingSessionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    s = await t_svc.update_session(
        db, session_id, payload=payload.model_dump(exclude_unset=True)
    )
    return _session_to_out(s)


@router.post(
    "/sessions",
    response_model=TrainingSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_session(
    payload: TrainingSessionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    s = await t_svc.schedule_session(db, payload=payload.model_dump())
    return _session_to_out(s)


@router.get("/sessions/me", response_model=list[TrainingSessionOut])
async def my_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    sessions = await t_svc.list_sessions(db, employee_id=emp.id)
    return [_session_to_out(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=TrainingSessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    s = await t_svc.get_session(db, session_id)
    return _session_to_out(s)


@router.patch(
    "/sessions/{session_id}/status", response_model=TrainingSessionOut
)
async def set_session_status(
    session_id: int,
    payload: TrainingSessionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    s = await t_svc.update_session_status(
        db, session_id, status=payload.status
    )
    return _session_to_out(s)


@router.post(
    "/sessions/{session_id}/register",
    response_model=ParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await t_svc.get_session(db, session_id)
    emp = await _self_employee(db, user)
    return await t_svc.register_participant(db, session=session, employee=emp)


@router.post("/sessions/check-in", response_model=ParticipantOut)
async def check_in(
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await t_svc.check_in_with_qr(
        db, qr_token=payload.qr_token, employee=emp
    )


@router.post(
    "/sessions/{session_id}/review",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def review_session(
    session_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await t_svc.get_session(db, session_id)
    emp = await _self_employee(db, user)
    return await t_svc.submit_review(
        db, session=session, employee=emp, payload=payload.model_dump()
    )

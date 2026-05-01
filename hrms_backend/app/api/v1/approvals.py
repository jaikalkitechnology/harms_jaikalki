from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Approval, User
from app.schemas.approval import (
    ApprovalCountByType,
    ApprovalDecisionRequest,
    ApprovalDelegateRequest,
    ApprovalOut,
)
from app.services import approval_engine
import app.services.approval_handlers  # noqa: F401  (registers handlers)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/inbox", response_model=list[ApprovalOut])
async def inbox(
    request_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
) -> Sequence[Approval]:
    return await approval_engine.list_pending_for_user(
        db, user, request_type=request_type
    )


@router.get("/inbox/counts", response_model=list[ApprovalCountByType])
async def inbox_counts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    return await approval_engine.counts_by_type(db, user)


@router.get("/history", response_model=list[ApprovalOut])
async def history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await approval_engine.list_history_for_user(db, user)


@router.get("/{approval_id}", response_model=ApprovalOut)
async def get_one(
    approval_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Approval:
    return await approval_engine.get_approval(db, approval_id)


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(
    approval_id: int,
    payload: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
) -> Approval:
    return await approval_engine.decide(
        db, approval_id, user=user, approve=True, comments=payload.comments
    )


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(
    approval_id: int,
    payload: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
) -> Approval:
    return await approval_engine.decide(
        db, approval_id, user=user, approve=False, comments=payload.comments
    )


@router.post("/{approval_id}/delegate", response_model=ApprovalOut)
async def delegate(
    approval_id: int,
    payload: ApprovalDelegateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
) -> Approval:
    return await approval_engine.delegate(
        db,
        approval_id,
        user=user,
        to_user_id=payload.to_user_id,
        comments=payload.comments,
    )


@router.post("/{approval_id}/cancel", response_model=ApprovalOut)
async def cancel(
    approval_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Approval:
    return await approval_engine.cancel(db, approval_id, user=user)

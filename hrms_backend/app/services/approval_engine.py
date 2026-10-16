"""Universal approval engine.

Generic over the underlying record type (leave_request,
attendance_regularization, intern_expense, …). Each request type
registers a handler via `register_handler()` so the universal endpoint
can dispatch the actual decision back into the owning module — keeping
business logic in one place while the engine handles workflow,
audit trail, and the cross-module inbox.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import Role as RoleEnum
from app.models import Approval, ApprovalAction, ApprovalWorkflow, User
from app.services import employee_service as emp_svc

# Handler signature: (db, request_id, approver_user, approve, comments) -> any
ApprovalHandler = Callable[
    [AsyncSession, int, User, bool, Optional[str]],
    Awaitable[Any],
]

_HANDLERS: dict[str, ApprovalHandler] = {}


def register_handler(request_type: str, handler: ApprovalHandler) -> None:
    _HANDLERS[request_type] = handler


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Submission ────────────────────────────────────────────────────────
async def submit_for_approval(
    db: AsyncSession,
    *,
    request_type: str,
    request_id: int,
    employee_id: Optional[int],
    initiated_by: Optional[int],
    title: str,
    summary: Optional[str] = None,
    request_data: Optional[dict] = None,
) -> Approval:
    """Create an Approval row mirroring an underlying request."""

    # Idempotent: don't duplicate if one already exists.
    existing = (
        await db.execute(
            select(Approval)
            .where(Approval.request_type == request_type)
            .where(Approval.request_id == request_id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    workflow = (
        await db.execute(
            select(ApprovalWorkflow).where(ApprovalWorkflow.type == request_type)
        )
    ).scalar_one_or_none()

    max_levels = 1
    if workflow and workflow.levels_config:
        max_levels = max(1, len(workflow.levels_config))

    approval = Approval(
        request_type=request_type,
        request_id=request_id,
        employee_id=employee_id,
        request_data=request_data or {},
        title=title[:160],
        summary=summary,
        current_level=1,
        max_levels=max_levels,
        status="pending",
        initiated_by=initiated_by,
        initiated_at=_now(),
    )
    db.add(approval)
    await db.flush()
    return approval


async def mark_externally_decided(
    db: AsyncSession,
    *,
    request_type: str,
    request_id: int,
    approve: bool,
    decided_by: int,
    comments: Optional[str] = None,
) -> Optional[Approval]:
    """Sync the Approval row when a module-specific endpoint decides directly.

    e.g. an HR opens the legacy `/api/v1/leaves/{id}/approve` endpoint —
    we still record the action on the Approval row for a single audit log.
    """
    approval = (
        await db.execute(
            select(Approval)
            .where(Approval.request_type == request_type)
            .where(Approval.request_id == request_id)
        )
    ).scalar_one_or_none()
    if not approval or approval.status != "pending":
        return approval
    approval.status = "approved" if approve else "rejected"
    approval.final_status = approval.status
    approval.final_decision_at = _now()
    db.add(
        ApprovalAction(
            approval_id=approval.id,
            level=approval.current_level,
            approver_id=decided_by,
            action="approved" if approve else "rejected",
            comments=comments,
            action_at=_now(),
        )
    )
    await db.flush()
    return approval


# ── Reading the inbox ─────────────────────────────────────────────────
async def list_pending_for_user(
    db: AsyncSession,
    user: User,
    *,
    request_type: Optional[str] = None,
    limit: int = 200,
) -> Sequence[Approval]:
    visible = await emp_svc.visible_employee_ids(db, user, scope="direct")

    stmt = (
        select(Approval)
        .where(Approval.status == "pending")
        .order_by(Approval.initiated_at.desc())
        .limit(limit)
    )
    if request_type:
        stmt = stmt.where(Approval.request_type == request_type)
    if visible is not None:
        if not visible:
            return []
        stmt = stmt.where(Approval.employee_id.in_(visible))

    return (await db.execute(stmt)).scalars().all()


async def list_history_for_user(
    db: AsyncSession,
    user: User,
    *,
    limit: int = 100,
) -> Sequence[Approval]:
    """Approvals where this user has acted (any non-pending status)."""
    user_action_ids = (
        await db.execute(
            select(ApprovalAction.approval_id).where(
                ApprovalAction.approver_id == user.id
            )
        )
    ).scalars().all()
    if not user_action_ids:
        return []
    return (
        await db.execute(
            select(Approval)
            .where(Approval.id.in_(set(user_action_ids)))
            .order_by(Approval.final_decision_at.desc().nulls_last())
            .limit(limit)
        )
    ).scalars().all()


async def counts_by_type(db: AsyncSession, user: User) -> list[dict]:
    visible = await emp_svc.visible_employee_ids(db, user, scope="direct")
    stmt = (
        select(Approval.request_type, func.count(Approval.id))
        .where(Approval.status == "pending")
        .group_by(Approval.request_type)
    )
    if visible is not None:
        if not visible:
            return []
        stmt = stmt.where(Approval.employee_id.in_(visible))
    rows = (await db.execute(stmt)).all()
    return [{"request_type": r[0], "count": r[1]} for r in rows]


async def get_approval(db: AsyncSession, approval_id: int) -> Approval:
    obj = (
        await db.execute(select(Approval).where(Approval.id == approval_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Approval not found")
    return obj


# ── Decisions ────────────────────────────────────────────────────────
async def decide(
    db: AsyncSession,
    approval_id: int,
    *,
    user: User,
    approve: bool,
    comments: Optional[str] = None,
) -> Approval:
    approval = await get_approval(db, approval_id)

    if approval.status != "pending":
        raise ValidationError("Approval already finalised")

    handler = _HANDLERS.get(approval.request_type)
    if not handler:
        raise ValidationError(
            f"No handler registered for {approval.request_type}"
        )

    # Delegate to module handler. The handler may itself call
    # mark_externally_decided() if it routes through a legacy code path —
    # in which case the approval is already finalised when we return and
    # we shouldn't double-record the action.
    await handler(db, approval.request_id, user, approve, comments)
    await db.refresh(approval)
    if approval.status != "pending":
        return approval

    if approve:
        # Record the action.
        db.add(
            ApprovalAction(
                approval_id=approval.id,
                level=approval.current_level,
                approver_id=user.id,
                action="approved",
                comments=comments,
                action_at=_now(),
            )
        )
        if approval.current_level >= approval.max_levels:
            approval.status = "approved"
            approval.final_status = "approved"
            approval.final_decision_at = _now()
        else:
            approval.current_level += 1
    else:
        db.add(
            ApprovalAction(
                approval_id=approval.id,
                level=approval.current_level,
                approver_id=user.id,
                action="rejected",
                comments=comments,
                action_at=_now(),
            )
        )
        approval.status = "rejected"
        approval.final_status = "rejected"
        approval.final_decision_at = _now()

    await db.commit()
    await db.refresh(approval)
    return approval


async def cancel(
    db: AsyncSession,
    approval_id: int,
    *,
    user: User,
) -> Approval:
    approval = await get_approval(db, approval_id)
    if approval.status != "pending":
        raise ValidationError("Cannot cancel a finalised approval")
    if approval.initiated_by != user.id and not _is_admin(user):
        raise ForbiddenError("Only the initiator (or admin) can cancel")
    approval.status = "cancelled"
    approval.final_status = "cancelled"
    approval.final_decision_at = _now()
    db.add(
        ApprovalAction(
            approval_id=approval.id,
            level=approval.current_level,
            approver_id=user.id,
            action="cancelled",
            action_at=_now(),
        )
    )
    await db.commit()
    await db.refresh(approval)
    return approval


async def delegate(
    db: AsyncSession,
    approval_id: int,
    *,
    user: User,
    to_user_id: int,
    comments: Optional[str] = None,
) -> Approval:
    approval = await get_approval(db, approval_id)
    if approval.status != "pending":
        raise ValidationError("Cannot delegate a finalised approval")
    db.add(
        ApprovalAction(
            approval_id=approval.id,
            level=approval.current_level,
            approver_id=user.id,
            action="delegated",
            comments=comments,
            delegated_to=to_user_id,
            action_at=_now(),
        )
    )
    await db.commit()
    await db.refresh(approval)
    return approval


def _is_admin(user: User) -> bool:
    privileged = {
        RoleEnum.SUPER_ADMIN.value,
        RoleEnum.DIRECTOR.value,
        RoleEnum.HR.value,
        RoleEnum.ADMIN.value,
    }
    return bool(set(user.role_codes) & privileged)

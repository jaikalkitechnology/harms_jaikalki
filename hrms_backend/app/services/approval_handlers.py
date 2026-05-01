"""Register module-specific approval handlers with the engine.

Imported once at app startup so the dispatch table is populated.
Each handler receives (db, request_id, user, approve, comments) and is
responsible for the actual business decision (e.g. updating the
LeaveRequest record + deducting balance).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AttendanceRegularization,
    InternTravelExpense,
    LeaveRequest,
    User,
)
from app.services.approval_engine import register_handler


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Leave handler ─────────────────────────────────────────────────────
async def _leave_handler(
    db: AsyncSession,
    request_id: int,
    user: User,
    approve: bool,
    comments: Optional[str],
) -> None:
    from app.services import leave_service

    req = (
        await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
    ).scalar_one_or_none()
    if not req or req.status != "pending":
        from app.core.exceptions import ValidationError
        raise ValidationError("Underlying leave request is no longer pending")
    await leave_service.decide_leave(
        db, request_id, approver=user, approve=approve, decision_comment=comments
    )


# ── Attendance regularization handler ────────────────────────────────
async def _regularization_handler(
    db: AsyncSession,
    request_id: int,
    user: User,
    approve: bool,
    comments: Optional[str],
) -> None:
    from app.services import attendance_service

    if approve:
        await attendance_service.approve_regularization(
            db, request_id, approver=user, decision_comment=comments
        )
    else:
        await attendance_service.reject_regularization(
            db, request_id, approver=user, decision_comment=comments
        )


# ── Intern travel expense handler ────────────────────────────────────
async def _intern_expense_handler(
    db: AsyncSession,
    request_id: int,
    user: User,
    approve: bool,
    comments: Optional[str],
) -> None:
    from app.core.exceptions import NotFoundError, ValidationError

    exp = (
        await db.execute(
            select(InternTravelExpense).where(
                InternTravelExpense.id == request_id
            )
        )
    ).scalar_one_or_none()
    if not exp:
        raise NotFoundError("Expense not found")
    if exp.status != "pending":
        raise ValidationError("Expense already decided")
    if approve:
        exp.status = "approved"
        exp.approved_by = user.id
        exp.approved_at = _now()
    else:
        exp.status = "rejected"
        exp.approved_by = user.id
        exp.approved_at = _now()
        exp.rejection_reason = comments
    await db.flush()


def install_default_handlers() -> None:
    register_handler("leave_request", _leave_handler)
    register_handler("attendance_regularization", _regularization_handler)
    register_handler("intern_expense", _intern_expense_handler)


install_default_handlers()

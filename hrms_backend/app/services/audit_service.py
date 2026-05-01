"""Audit log service. Two paths to write:

1. Middleware auto-captures every authenticated mutation (POST/PUT/PATCH/
   DELETE) on /api/v1 routes — see app/core/middleware.py.
2. Explicit calls inside services for high-value events
   (e.g. payroll.run, justice.complaint.view, mfa.disable).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def log(
    db: AsyncSession,
    *,
    actor: Optional[User] = None,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str | int] = None,
    request_id: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    payload: Optional[dict] = None,
) -> AuditLog:
    row = AuditLog(
        actor_user_id=actor.id if actor else None,
        actor_label=actor.full_name if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        request_id=request_id,
        ip=ip,
        user_agent=user_agent,
        method=method,
        path=path,
        status_code=status_code,
        payload=payload,
        occurred_at=_now(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_logs(
    db: AsyncSession,
    *,
    actor_user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    since_days: Optional[int] = None,
    limit: int = 200,
) -> Sequence[AuditLog]:
    stmt = select(AuditLog)
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == str(entity_id))
    if since_days is not None:
        stmt = stmt.where(
            AuditLog.occurred_at >= _now() - timedelta(days=since_days)
        )
    stmt = stmt.order_by(desc(AuditLog.occurred_at)).limit(limit)
    return (await db.execute(stmt)).scalars().all()

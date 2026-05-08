"""Notification service: persist + dispatch to in-app, email, push."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import DeviceToken, Notification, User
from app.services.email_service import (
    send_email,
    send_template_email,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def notify(
    db: AsyncSession,
    *,
    user_id: int,
    type: str,
    title: str,
    body: Optional[str] = None,
    data: Optional[dict] = None,
    email_template: Optional[str] = None,
    email_params: Optional[dict] = None,
    send_email_now: bool = False,
    send_push: bool = False,
) -> Notification:
    """Create an in-app notification and (optionally) email + push.

    The in-app row is always created so it's visible in the bell. Email
    and push are best-effort — failures are logged on the notification
    row but don't raise.
    """
    notif = Notification(
        user_id=user_id,
        channel="in_app",
        type=type,
        title=title,
        body=body,
        data=data,
        sent_at=_now(),
        status="sent",
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    if send_email_now:
        user = (
            await db.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if user:
            params = dict(email_params or {})
            params.setdefault("name", user.full_name or user.email)
            ok, err = (
                await send_template_email(
                    to_email=user.email,
                    to_name=user.full_name,
                    template=email_template,
                    params=params,
                )
                if email_template
                else await send_email(
                    to_email=user.email,
                    to_name=user.full_name,
                    subject=title,
                    html=f"<p>{body or ''}</p>",
                )
            )
            email_row = Notification(
                user_id=user_id,
                channel="email",
                type=type,
                title=title,
                body=body,
                data=data,
                sent_at=_now() if ok else None,
                status="sent" if ok else "failed",
                error=err,
            )
            db.add(email_row)
            await db.commit()

    if send_push:
        from app.services import push_service

        tokens = (
            await db.execute(
                select(DeviceToken)
                .where(DeviceToken.user_id == user_id)
                .where(DeviceToken.is_active.is_(True))
            )
        ).scalars().all()
        if tokens:
            ok_count, fail_count = push_service.send_push_multicast(
                tokens=[t.token for t in tokens],
                title=title,
                body=body,
                data=(data or {}) | {"type": type},
            )
            push_row = Notification(
                user_id=user_id,
                channel="push",
                type=type,
                title=title,
                body=body,
                data=data,
                sent_at=_now() if ok_count > 0 else None,
                status="sent"
                if ok_count > 0
                else ("failed" if fail_count > 0 else "pending"),
                error=(
                    None
                    if ok_count > 0
                    else f"FCM unavailable / no tokens ok (failed={fail_count})"
                ),
            )
            db.add(push_row)
            await db.commit()

    return notif


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
) -> Sequence[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.channel == "in_app")
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


async def unread_count(db: AsyncSession, *, user_id: int) -> int:
    from sqlalchemy import func

    return (
        await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
            .where(Notification.channel == "in_app")
            .where(Notification.read_at.is_(None))
        )
    ).scalar() or 0


async def mark_read(
    db: AsyncSession, notification_id: int, *, user_id: int
) -> Notification:
    n = (
        await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
    ).scalar_one_or_none()
    if not n:
        raise NotFoundError("Notification not found")
    if n.user_id != user_id:
        raise ForbiddenError("Not your notification")
    if n.read_at is None:
        n.read_at = _now()
        n.status = "read"
        await db.commit()
        await db.refresh(n)
    return n


async def mark_all_read(db: AsyncSession, *, user_id: int) -> int:
    rows = (
        await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.channel == "in_app")
            .where(Notification.read_at.is_(None))
        )
    ).scalars().all()
    now = _now()
    for n in rows:
        n.read_at = now
        n.status = "read"
    await db.commit()
    return len(rows)


async def broadcast(
    db: AsyncSession,
    *,
    audience: str,
    title: str,
    body: Optional[str] = None,
    data: Optional[dict] = None,
    type: str = "broadcast",
    send_push: bool = True,
    user_ids: Optional[Sequence[int]] = None,
    role_codes: Optional[Sequence[str]] = None,
    department_id: Optional[int] = None,
) -> dict:
    """Fan out a notification to many users.

    audience:
      - "all": every user with a linked employee
      - "role": users whose role matches role_codes
      - "department": users whose linked employee is in department_id
      - "users": explicit user_ids list
    """
    from sqlalchemy import distinct
    from app.models import Employee, UserRole, Role

    target_ids: list[int] = []
    if audience == "users":
        target_ids = list(user_ids or [])
    elif audience == "all":
        rows = (
            await db.execute(
                select(distinct(Employee.user_id))
                .where(Employee.user_id.is_not(None))
            )
        ).scalars().all()
        target_ids = list(rows)
    elif audience == "role":
        if not role_codes:
            return {"queued": 0, "sent": 0}
        rows = (
            await db.execute(
                select(distinct(UserRole.user_id))
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.code.in_(list(role_codes)))
            )
        ).scalars().all()
        target_ids = list(rows)
    elif audience == "department":
        if department_id is None:
            return {"queued": 0, "sent": 0}
        rows = (
            await db.execute(
                select(distinct(Employee.user_id))
                .where(Employee.department_id == department_id)
                .where(Employee.user_id.is_not(None))
            )
        ).scalars().all()
        target_ids = list(rows)
    else:
        return {"queued": 0, "sent": 0}

    sent = 0
    for uid in target_ids:
        try:
            await notify(
                db,
                user_id=uid,
                type=type,
                title=title,
                body=body,
                data=data,
                send_push=send_push,
            )
            sent += 1
        except Exception:
            logger.exception("broadcast: failed for user %s", uid)
    return {"queued": len(target_ids), "sent": sent}


# ─── Device tokens ───────────────────────────────────────────────────
async def register_device_token(
    db: AsyncSession,
    *,
    user_id: int,
    platform: str,
    token: str,
) -> DeviceToken:
    existing = (
        await db.execute(
            select(DeviceToken).where(DeviceToken.token == token)
        )
    ).scalar_one_or_none()
    if existing:
        existing.user_id = user_id
        existing.platform = platform
        existing.is_active = True
        existing.last_seen_at = _now()
        await db.commit()
        await db.refresh(existing)
        return existing
    dt = DeviceToken(
        user_id=user_id,
        platform=platform,
        token=token,
        is_active=True,
        last_seen_at=_now(),
    )
    db.add(dt)
    await db.commit()
    await db.refresh(dt)
    return dt


async def unregister_device_token(
    db: AsyncSession, *, token: str, user_id: int
) -> None:
    dt = (
        await db.execute(
            select(DeviceToken).where(DeviceToken.token == token)
        )
    ).scalar_one_or_none()
    if not dt:
        return
    if dt.user_id != user_id:
        raise ForbiddenError("Not your token")
    dt.is_active = False
    await db.commit()

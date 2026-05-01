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
        # Stub: enqueue a row marked sent if we have any active tokens.
        tokens = (
            await db.execute(
                select(DeviceToken)
                .where(DeviceToken.user_id == user_id)
                .where(DeviceToken.is_active.is_(True))
            )
        ).scalars().all()
        if tokens:
            push_row = Notification(
                user_id=user_id,
                channel="push",
                type=type,
                title=title,
                body=body,
                data=data,
                sent_at=_now(),
                status="sent" if settings.FCM_SERVER_KEY else "pending",
                error=None
                if settings.FCM_SERVER_KEY
                else "FCM_SERVER_KEY not configured",
            )
            db.add(push_row)
            await db.commit()
            # NOTE: actual FCM HTTP call elided until prod Firebase project
            # is provisioned — see DEPLOY.md for setup.

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

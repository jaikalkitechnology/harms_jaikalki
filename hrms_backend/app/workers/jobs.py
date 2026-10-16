"""Scheduled jobs."""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@celery_app.task(name="app.workers.jobs.send_compliance_digest")
def send_compliance_digest() -> dict:
    """Email an HR digest with pending approvals, breached SLAs, and
    employees missing mandatory certifications. Returns a summary dict
    so the result is inspectable from `celery events` / Flower."""
    return asyncio.run(_run_compliance_digest())


async def _run_compliance_digest() -> dict:
    from app.database import AsyncSessionLocal
    from app.models import (
        Approval,
        Course,
        CourseEnrollment,
        Employee,
        PerformanceReview,
        Role,
        ReviewCycle,
        User,
        UserRole,
        Verification,
    )
    from app.services.email_service import send_template_email

    today = date.today()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import func

        pending_approvals = (
            await db.execute(
                select(func.count(Approval.id)).where(
                    Approval.status == "pending"
                )
            )
        ).scalar() or 0

        # Verifications past their deadline that haven't been completed.
        overdue_verifications = (
            await db.execute(
                select(func.count(Verification.id))
                .where(Verification.status != "completed")
                .where(Verification.deadline_at < _now_utc())
            )
        ).scalar() or 0

        # Pending self-reviews for the active cycle (best-effort)
        active_cycle = (
            await db.execute(
                select(ReviewCycle)
                .where(
                    ReviewCycle.status.in_(["open", "review", "calibration"])
                )
                .order_by(ReviewCycle.period_start.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        pending_self_reviews = 0
        if active_cycle:
            active_emps = (
                await db.execute(
                    select(func.count(Employee.id)).where(
                        Employee.status == "active"
                    )
                )
            ).scalar() or 0
            self_submitted = (
                await db.execute(
                    select(func.count(PerformanceReview.id))
                    .where(PerformanceReview.cycle_id == active_cycle.id)
                    .where(PerformanceReview.review_type == "self")
                    .where(PerformanceReview.status != "draft")
                )
            ).scalar() or 0
            pending_self_reviews = max(0, active_emps - self_submitted)

        # Employees without an active POSH certificate (mandatory courses)
        mandatory = (
            await db.execute(
                select(Course)
                .where(Course.is_mandatory.is_(True))
                .where(Course.is_published.is_(True))
            )
        ).scalars().all()
        active_emps_total = (
            await db.execute(
                select(func.count(Employee.id)).where(
                    Employee.status == "active"
                )
            )
        ).scalar() or 0
        posh_uncertified = active_emps_total
        if mandatory:
            mandatory_ids = [c.id for c in mandatory]
            certified_rows = (
                await db.execute(
                    select(CourseEnrollment.employee_id)
                    .where(CourseEnrollment.status == "completed")
                    .where(CourseEnrollment.course_id.in_(mandatory_ids))
                )
            ).scalars().all()
            certified = len(set(certified_rows))
            posh_uncertified = max(0, active_emps_total - certified)

        # Recipients: anyone with the HR or super_admin role.
        hr_users = (
            await db.execute(
                select(User)
                .join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.code.in_(["hr", "super_admin"]))
                .where(User.is_active.is_(True))
            )
        ).scalars().all()

        params = {
            "date": today.isoformat(),
            "pending_approvals": pending_approvals,
            "overdue_verifications": overdue_verifications,
            "pending_self_reviews": pending_self_reviews,
            "posh_uncertified": posh_uncertified,
        }

        sent = 0
        for u in hr_users:
            ok, _ = await send_template_email(
                to_email=u.email,
                to_name=u.full_name,
                template="compliance_digest",
                params=params,
            )
            if ok:
                sent += 1

        return {**params, "recipients_attempted": len(hr_users), "sent": sent}


@celery_app.task(name="app.workers.jobs.purge_expired_otps")
def purge_expired_otps() -> dict:
    return asyncio.run(_run_purge_expired_otps())


async def _run_purge_expired_otps() -> dict:
    from app.database import AsyncSessionLocal
    from app.models import PasswordResetOtp

    cutoff = _now_utc() - timedelta(days=7)
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(PasswordResetOtp).where(
                    PasswordResetOtp.created_at < cutoff
                )
            )
        ).scalars().all()
        for r in rows:
            await db.delete(r)
        await db.commit()
    return {"purged": len(rows)}


@celery_app.task(name="app.workers.jobs.run_team_alerts")
def run_team_alerts() -> dict:
    """Every 10 minutes: run whichever team alerts are due (morning
    digest, plan reminder, overdue-task escalation, weekly summary,
    nightly target refresh). Each runs once at its configured time."""
    return asyncio.run(_run_team_alerts())


async def _run_team_alerts() -> dict:
    from app.database import AsyncSessionLocal, engine
    from app.services.team_alerts import run_due

    try:
        async with AsyncSessionLocal() as db:
            return await run_due(db)
    finally:
        # asyncio.run gives every call a new loop; pooled connections
        # from the old one can't be reused.
        await engine.dispose()

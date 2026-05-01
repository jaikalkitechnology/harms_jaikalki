"""Daily Work Planning (DWP) service.

Configurable per-department morning + EOD submissions, with auto-link
between yesterday's "tomorrow plan" → today's morning prefill, and
today's morning → today's EOD prefill.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    DwpComment,
    DwpSubmission,
    DwpSubmissionField,
    DwpTemplate,
    Employee,
    User,
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Templates ─────────────────────────────────────────────────────────
async def find_template(
    db: AsyncSession,
    employee: Employee,
    *,
    type: str,
) -> DwpTemplate:
    """Pick the most-specific template for this employee + type.

    Resolution order:
      1. Department-specific active template
      2. Global default template (department_id NULL)
    """
    stmt = select(DwpTemplate).where(
        DwpTemplate.is_active.is_(True), DwpTemplate.type == type
    )
    if employee.department_id:
        dept_match = await db.execute(
            stmt.where(DwpTemplate.department_id == employee.department_id)
        )
        t = dept_match.scalars().first()
        if t:
            return t
    fallback = await db.execute(
        stmt.where(DwpTemplate.department_id.is_(None))
    )
    t = fallback.scalars().first()
    if not t:
        raise NotFoundError(
            f"No active {type} DWP template configured for this employee"
        )
    return t


# ── Submissions ───────────────────────────────────────────────────────
async def get_submission(
    db: AsyncSession,
    *,
    employee_id: int,
    on_date: date,
    type: str,
) -> Optional[DwpSubmission]:
    return (
        await db.execute(
            select(DwpSubmission)
            .where(DwpSubmission.employee_id == employee_id)
            .where(DwpSubmission.date == on_date)
            .where(DwpSubmission.type == type)
        )
    ).scalar_one_or_none()


async def submit(
    db: AsyncSession,
    employee: Employee,
    *,
    template: DwpTemplate,
    fields: dict[str, Any],
    total_hours: Optional[Decimal] = None,
    mood_rating: Optional[int] = None,
    on_date: Optional[date] = None,
) -> DwpSubmission:
    on_date = on_date or _today()

    # Validate required fields
    field_specs = {f.key: f for f in template.fields}
    for key, spec in field_specs.items():
        if spec.is_required:
            v = fields.get(key)
            if v is None or (isinstance(v, str) and not v.strip()):
                raise ValidationError(f"Field '{spec.label}' is required")

    existing = await get_submission(
        db, employee_id=employee.id, on_date=on_date, type=template.type
    )
    if existing:
        raise ConflictError(
            f"Already submitted {template.type} DWP for {on_date}"
        )

    # Auto-link EOD → morning
    linked_morning_id: Optional[int] = None
    if template.type == "eod":
        morning = await get_submission(
            db, employee_id=employee.id, on_date=on_date, type="morning"
        )
        if morning:
            linked_morning_id = morning.id

    submission = DwpSubmission(
        employee_id=employee.id,
        template_id=template.id,
        type=template.type,
        date=on_date,
        submitted_at=_now(),
        total_hours=total_hours,
        mood_rating=mood_rating,
        linked_morning_id=linked_morning_id,
    )
    db.add(submission)
    await db.flush()

    for key, raw in fields.items():
        if key not in field_specs:
            continue  # Silently drop unknown keys
        value, file_url = _serialize_value(raw)
        db.add(
            DwpSubmissionField(
                submission_id=submission.id,
                field_key=key,
                value=value,
                file_url=file_url,
            )
        )

    await db.commit()
    await db.refresh(submission)
    return submission


def _serialize_value(raw: Any) -> tuple[Optional[str], Optional[str]]:
    """Pack a typed value into (value_str, file_url).

    For dict / list payloads we JSON-encode into `value`. Photo/voice URLs
    can be passed as a dict {"url": "..."} which is broken out separately.
    """
    if raw is None:
        return None, None
    if isinstance(raw, dict) and "url" in raw and len(raw) <= 2:
        url = raw["url"]
        rest = {k: v for k, v in raw.items() if k != "url"}
        return (json.dumps(rest) if rest else None), str(url) if url else None
    if isinstance(raw, (list, dict)):
        return json.dumps(raw), None
    if isinstance(raw, bool):
        return "true" if raw else "false", None
    return str(raw), None


# ── Reads ─────────────────────────────────────────────────────────────
async def my_history(
    db: AsyncSession,
    employee_id: int,
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 90,
) -> Sequence[DwpSubmission]:
    stmt = (
        select(DwpSubmission)
        .where(DwpSubmission.employee_id == employee_id)
        .order_by(DwpSubmission.date.desc(), DwpSubmission.type.desc())
        .limit(limit)
    )
    if from_date:
        stmt = stmt.where(DwpSubmission.date >= from_date)
    if to_date:
        stmt = stmt.where(DwpSubmission.date <= to_date)
    return (await db.execute(stmt)).scalars().all()


async def team_today(
    db: AsyncSession,
    *,
    employee_ids: Sequence[int],
    on_date: Optional[date] = None,
) -> Sequence[DwpSubmission]:
    if not employee_ids:
        return []
    on_date = on_date or _today()
    return (
        await db.execute(
            select(DwpSubmission)
            .where(DwpSubmission.employee_id.in_(list(employee_ids)))
            .where(DwpSubmission.date == on_date)
            .order_by(DwpSubmission.submitted_at.desc())
        )
    ).scalars().all()


async def team_blockers(
    db: AsyncSession,
    *,
    employee_ids: Sequence[int],
    on_date: Optional[date] = None,
) -> Sequence[DwpSubmission]:
    """EOD submissions where the `blockers` field has a non-empty value."""
    if not employee_ids:
        return []
    on_date = on_date or _today()
    rows = (
        await db.execute(
            select(DwpSubmission)
            .where(DwpSubmission.employee_id.in_(list(employee_ids)))
            .where(DwpSubmission.date == on_date)
            .where(DwpSubmission.type == "eod")
        )
    ).scalars().all()
    blocked: list[DwpSubmission] = []
    for s in rows:
        for f in s.fields:
            if f.field_key == "blockers" and f.value and f.value.strip():
                blocked.append(s)
                break
    return blocked


# ── Auto-link prefills ────────────────────────────────────────────────
async def prefill_for(
    db: AsyncSession,
    employee_id: int,
    *,
    type: str,
    on_date: Optional[date] = None,
) -> tuple[dict[str, Any], Optional[int]]:
    """Return a prefill dict for today's morning or EOD.

    - Morning: pulls `tomorrow_plan` from yesterday's EOD (if any).
    - EOD: pulls `tasks` from today's morning (if any).
    """
    on_date = on_date or _today()
    if type == "morning":
        yesterday = on_date - timedelta(days=1)
        prev = await get_submission(
            db, employee_id=employee_id, on_date=yesterday, type="eod"
        )
        if not prev:
            return {}, None
        for f in prev.fields:
            if f.field_key == "tomorrow_plan" and f.value:
                return {"tasks": f.value}, None
        return {}, None

    # EOD prefill from today's morning
    morning = await get_submission(
        db, employee_id=employee_id, on_date=on_date, type="morning"
    )
    if not morning:
        return {}, None
    prefill: dict[str, Any] = {}
    for f in morning.fields:
        if f.field_key in {"tasks", "project", "status_tag"} and f.value:
            prefill[f.field_key] = f.value
    return prefill, morning.id


# ── Streak ────────────────────────────────────────────────────────────
async def streak_for(
    db: AsyncSession, employee_id: int, *, today: Optional[date] = None
) -> tuple[int, Optional[date]]:
    """Count consecutive days back from today with at least one DWP submission."""
    today = today or _today()
    rows = (
        await db.execute(
            select(DwpSubmission.date)
            .where(DwpSubmission.employee_id == employee_id)
            .order_by(DwpSubmission.date.desc())
            .limit(120)
        )
    ).scalars().all()
    days = sorted({d for d in rows}, reverse=True)
    if not days:
        return 0, None
    last = days[0]
    streak = 0
    cursor = today
    if last < today - timedelta(days=1):
        return 0, last
    if last == today - timedelta(days=1):
        cursor = last  # break: streak counts back from yesterday
    for d in days:
        if d == cursor:
            streak += 1
            cursor = cursor - timedelta(days=1)
        elif d < cursor:
            break
    return streak, last


# ── Comments ──────────────────────────────────────────────────────────
async def add_comment(
    db: AsyncSession,
    *,
    submission_id: int,
    user: User,
    comment: str,
    is_kudos: bool,
) -> DwpComment:
    submission = (
        await db.execute(
            select(DwpSubmission).where(DwpSubmission.id == submission_id)
        )
    ).scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    obj = DwpComment(
        submission_id=submission.id,
        commented_by=user.id,
        comment=comment,
        is_kudos=is_kudos,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

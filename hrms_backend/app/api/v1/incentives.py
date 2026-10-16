"""Incentives — see app/services/incentive_service.py."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import IncentiveLine, IncentiveRun, IncentiveScheme, User
from app.services import employee_service as emp_svc
from app.services import incentive_service as svc

router = APIRouter(prefix="/incentives", tags=["incentives"])
MANAGE = svc.MANAGE


class Slab(BaseModel):
    min_pct: float
    value: float


class SchemeIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=4000)
    metric: str = "sales_amount"
    period_type: str = "monthly"
    payout_type: str = "fixed"
    slabs: list[Slab]
    max_payout: Optional[Decimal] = Field(default=None, ge=0)
    department_ids: Optional[list[int]] = None
    category_codes: Optional[list[str]] = None
    designation_ids: Optional[list[int]] = None
    min_attendance_pct: Optional[int] = Field(default=None, ge=0, le=100)
    confirmed_only: bool = False
    exclude_notice: bool = True
    no_warning_days: Optional[int] = Field(default=None, ge=1, le=730)
    min_tenure_days: Optional[int] = Field(default=None, ge=1, le=3650)
    is_active: bool = True


class SchemeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=4000)
    metric: Optional[str] = None
    period_type: Optional[str] = None
    payout_type: Optional[str] = None
    slabs: Optional[list[Slab]] = None
    max_payout: Optional[Decimal] = Field(default=None, ge=0)
    department_ids: Optional[list[int]] = None
    category_codes: Optional[list[str]] = None
    designation_ids: Optional[list[int]] = None
    min_attendance_pct: Optional[int] = Field(default=None, ge=0, le=100)
    confirmed_only: Optional[bool] = None
    exclude_notice: Optional[bool] = None
    no_warning_days: Optional[int] = Field(default=None, ge=1, le=730)
    min_tenure_days: Optional[int] = Field(default=None, ge=1, le=3650)
    is_active: Optional[bool] = None


class RunIn(BaseModel):
    scheme_id: int
    # Any day inside the period to calculate.
    period_date: date
    payout_year: Optional[int] = Field(default=None, ge=2000, le=2100)
    payout_month: Optional[int] = Field(default=None, ge=1, le=12)


class RunUpdate(BaseModel):
    payout_year: int = Field(ge=2000, le=2100)
    payout_month: int = Field(ge=1, le=12)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ApproveIn(BaseModel):
    approve_pending: bool = False


class ReviewIn(BaseModel):
    action: str = Field(pattern="^(approve|adjust|reject|reset)$")
    amount: Optional[Decimal] = Field(default=None, ge=0)
    note: Optional[str] = Field(default=None, max_length=500)


def _scheme_out(s: IncentiveScheme) -> dict:
    return {
        c: getattr(s, c)
        for c in (
            "id", "name", "description", "metric", "period_type", "payout_type", "slabs",
            "max_payout", "department_ids", "category_codes", "designation_ids",
            "min_attendance_pct", "confirmed_only", "exclude_notice", "no_warning_days",
            "min_tenure_days", "is_active", "created_at",
        )
    }


# ── Schemes ──────────────────────────────────────────────────────────
@router.get("/schemes")
async def list_schemes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    rows = (await db.execute(select(IncentiveScheme).order_by(IncentiveScheme.is_active.desc(), IncentiveScheme.name))).scalars()
    return [_scheme_out(s) for s in rows]


@router.post("/schemes", status_code=status.HTTP_201_CREATED)
async def create_scheme(
    payload: SchemeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    data = svc.validate_scheme(payload.model_dump())
    s = IncentiveScheme(**data, created_by=user.id)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _scheme_out(s)


@router.put("/schemes/{scheme_id}")
async def update_scheme(
    scheme_id: int,
    payload: SchemeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    s = await svc.get_scheme(db, scheme_id)
    changes = payload.model_dump(exclude_unset=True)
    merged = svc.validate_scheme({**_scheme_out(s), **changes})
    for k in changes:
        setattr(s, k, merged[k])
    await db.commit()
    await db.refresh(s)
    return _scheme_out(s)


@router.delete("/schemes/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheme(
    scheme_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    s = await svc.get_scheme(db, scheme_id)
    used = (await db.execute(select(IncentiveRun.id).where(IncentiveRun.scheme_id == s.id).limit(1))).first()
    if used:
        raise ConflictError("This scheme has runs — switch it off instead of deleting")
    await db.delete(s)
    await db.commit()


# ── Runs ─────────────────────────────────────────────────────────────
@router.get("/runs")
async def list_runs(
    scheme_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    stmt = select(IncentiveRun).where(IncentiveRun.status != "cancelled")
    if scheme_id:
        stmt = stmt.where(IncentiveRun.scheme_id == scheme_id)
    runs = (await db.execute(stmt.order_by(IncentiveRun.period_start.desc(), IncentiveRun.id.desc()).limit(100))).scalars()
    return [await svc.run_summary(db, r) for r in runs]


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def calculate(
    payload: RunIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    s = await svc.get_scheme(db, payload.scheme_id)
    payout = (
        (payload.payout_year, payload.payout_month)
        if payload.payout_year and payload.payout_month
        else None
    )
    run = await svc.calculate_run(db, s, period_start=payload.period_date, payout=payout, actor=user)
    return await svc.run_summary(db, run)


@router.get("/runs/{run_id}")
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    run = await svc.get_run(db, run_id)
    lines = (
        await db.execute(select(IncentiveLine).where(IncentiveLine.run_id == run.id))
    ).scalars().all()
    out = await svc.serialize_lines(db, lines)
    out.sort(key=lambda r: (-float(r["amount"] or 0), r["employee_name"]))
    return {**await svc.run_summary(db, run), "lines_detail": out}


@router.patch("/runs/{run_id}")
async def update_run(
    run_id: int,
    payload: RunUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    run = await svc.get_run(db, run_id)
    if run.status != "review":
        raise ConflictError("Reopen the run to change it")
    run.payout_year, run.payout_month = payload.payout_year, payload.payout_month
    if payload.notes is not None:
        run.notes = payload.notes
    await db.commit()
    return await svc.run_summary(db, run)


@router.post("/runs/{run_id}/recalculate")
async def recalculate(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    run = await svc.get_run(db, run_id)
    s = await svc.get_scheme(db, run.scheme_id)
    run = await svc.calculate_run(db, s, period_start=run.period_start, actor=user, notify=False)
    return await svc.run_summary(db, run)


@router.post("/runs/{run_id}/approve")
async def approve(
    run_id: int,
    payload: ApproveIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    run = await svc.approve_run(db, user, run_id, approve_pending=payload.approve_pending)
    return await svc.run_summary(db, run)


@router.post("/runs/{run_id}/reopen")
async def reopen(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    return await svc.run_summary(db, await svc.reopen_run(db, run_id))


@router.post("/runs/{run_id}/cancel")
async def cancel(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    run = await svc.reopen_run(db, run_id)  # refuses if already paid
    run.status = "cancelled"
    await db.commit()
    return await svc.run_summary(db, run)


# ── Manager review ───────────────────────────────────────────────────
@router.get("/review")
async def review_queue(
    run_id: Optional[int] = None,
    pending_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lines waiting for the caller: their direct reports' lines in runs
    under review (all of them for HR / payroll)."""
    allowed = await svc.reviewable_ids(db, user)
    stmt = (
        select(IncentiveLine)
        .join(IncentiveRun, IncentiveRun.id == IncentiveLine.run_id)
        .where(IncentiveRun.status == "review")
    )
    if allowed is not None:
        stmt = stmt.where(IncentiveLine.employee_id.in_(allowed or {-1}))
    if run_id:
        stmt = stmt.where(IncentiveLine.run_id == run_id)
    if pending_only:
        stmt = stmt.where(IncentiveLine.review_status == "pending")
    lines = (await db.execute(stmt.order_by(IncentiveRun.period_start.desc()))).scalars().all()
    out = await svc.serialize_lines(db, lines)
    out.sort(key=lambda r: (r["review_status"] != "pending", r["employee_name"]))
    return out


@router.post("/lines/{line_id}/review")
async def review(
    line_id: int,
    payload: ReviewIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    me = await emp_svc.get_self_employee(db, user)
    ln = (await db.execute(select(IncentiveLine).where(IncentiveLine.id == line_id))).scalar_one_or_none()
    if ln and me and ln.employee_id == me.id:
        raise ValidationError("You can't review your own incentive")
    ln = await svc.review_line(
        db, user, line_id, action=payload.action, amount=payload.amount, note=payload.note
    )
    return (await svc.serialize_lines(db, [ln]))[0]


# ── Me ───────────────────────────────────────────────────────────────
@router.get("/me")
async def my_incentives(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    me = await emp_svc.get_self_employee(db, user)
    if not me:
        raise NotFoundError("No employee record linked to this account")
    return await svc.my_incentives(db, me)


@router.get("/review/count")
async def review_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    allowed = await svc.reviewable_ids(db, user)
    if allowed is not None and not allowed:
        return {"pending": 0}
    from sqlalchemy import func

    stmt = (
        select(func.count())
        .select_from(IncentiveLine)
        .join(IncentiveRun, IncentiveRun.id == IncentiveLine.run_id)
        .where(IncentiveRun.status == "review", IncentiveLine.review_status == "pending")
    )
    if allowed is not None:
        stmt = stmt.where(IncentiveLine.employee_id.in_(allowed))
    return {"pending": (await db.execute(stmt)).scalar() or 0}


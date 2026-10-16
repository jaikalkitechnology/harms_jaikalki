"""Incentives — HR's schemes turned into monthly payouts.

1. HR sets up a scheme: which target it pays on, the slabs (80 % →
   ₹2,000 …) and the eligibility rules (attendance, confirmed staff, not
   serving notice, no recent warning letter, minimum tenure; optionally
   only some departments / categories / designations).
2. A run calculates every covered employee for a period: target
   progress, slab reached, eligibility with reasons.
3. Each employee's direct manager approves, adjusts (with a note) or
   rejects their line. HR can review any line.
4. HR approves the run; the amounts are paid with the chosen payroll
   month as an "Incentive" earning on the payslip.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional

from sqlalchemy import Integer, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import (
    Attendance,
    Employee,
    EmployeeCategory,
    EmployeeLetter,
    Holiday,
    IncentiveLine,
    IncentiveRun,
    IncentiveScheme,
    LeaveRequest,
    PayrollRun,
    Resignation,
    SalesTarget,
    User,
)
from app.models.incentives import PAYOUT_TYPES
from app.models.sales import TARGET_METRICS
from app.services import employee_service as emp_svc

MANAGE = "payroll.run"
LEFT = ("resigned", "terminated", "separated", "inactive")
NOTICE_STATES = ("accepted", "in_notice", "ndc_pending", "cleared", "settled")
METRIC_UNITS = {
    "sales_amount": "₹",
    "leads_won": "leads won",
    "new_leads": "new leads",
    "field_visits": "visits",
    "verifications": "verifications",
    "tasks_done": "tasks done",
}


def _now() -> datetime:
    return datetime.utcnow()


def _money(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def can_manage(user: User) -> bool:
    codes = user.permission_codes
    return MANAGE in codes or "system.config" in codes


def _name(e: Optional[Employee]) -> str:
    return f"{e.first_name} {e.last_name}".strip() if e else ""


# ── Periods & slabs ──────────────────────────────────────────────────
def period_for(period_type: str, ref: date) -> tuple[date, date]:
    """The month (or calendar quarter) containing ``ref``."""
    if period_type == "quarterly":
        q0 = (ref.month - 1) // 3 * 3 + 1
        start = date(ref.year, q0, 1)
        end_month = q0 + 2
    else:
        start = ref.replace(day=1)
        end_month = ref.month
    nxt = date(start.year + (end_month == 12), end_month % 12 + 1, 1)
    return start, nxt - timedelta(days=1)


def previous_period(period_type: str, today: date) -> tuple[date, date]:
    start, _ = period_for(period_type, today)
    return period_for(period_type, start - timedelta(days=1))


def clean_slabs(slabs: list) -> list[dict]:
    out = []
    for s in slabs or []:
        try:
            p = round(float(s["min_pct"]), 2)
            v = round(float(s["value"]), 2)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError("Each slab needs a minimum % and a value") from exc
        if not (0 < p <= 1000) or v < 0:
            raise ValidationError("Slab % must be 1–1000 and the value 0 or more")
        out.append({"min_pct": p, "value": v})
    if not out:
        raise ValidationError("Add at least one slab")
    out.sort(key=lambda s: s["min_pct"])
    if len({s["min_pct"] for s in out}) != len(out):
        raise ValidationError("Two slabs have the same %")
    return out


def slab_reached(scheme: IncentiveScheme, pct: float) -> Optional[dict]:
    reached = [s for s in scheme.slabs or [] if pct >= float(s["min_pct"])]
    return reached[-1] if reached else None


def next_slab(scheme: IncentiveScheme, pct: float) -> Optional[dict]:
    ahead = [s for s in scheme.slabs or [] if pct < float(s["min_pct"])]
    return ahead[0] if ahead else None


def payout_for(scheme: IncentiveScheme, slab: Optional[dict], achieved) -> Decimal:
    if not slab:
        return Decimal(0)
    if scheme.payout_type == "percent_of_achieved":
        amount = Decimal(str(achieved or 0)) * Decimal(str(slab["value"])) / 100
    else:
        amount = Decimal(str(slab["value"]))
    if scheme.max_payout is not None:
        amount = min(amount, Decimal(str(scheme.max_payout)))
    return _money(amount)


# ── Who / eligibility ────────────────────────────────────────────────
def applies_to(scheme: IncentiveScheme, emp: Employee, category_code: Optional[str]) -> bool:
    if scheme.department_ids and emp.department_id not in scheme.department_ids:
        return False
    if scheme.designation_ids and emp.designation_id not in scheme.designation_ids:
        return False
    if scheme.category_codes and category_code not in scheme.category_codes:
        return False
    return True


async def attendance_pct(db: AsyncSession, emp: Employee, start: date, end: date) -> Optional[float]:
    """Days present ÷ days they were expected to work (working days in
    the period while employed, less approved leave). Half days count ½.
    None when there were no such days."""
    end = min(end, date.today())
    if emp.date_of_joining:
        start = max(start, emp.date_of_joining)
    if emp.exit_date:
        end = min(end, emp.exit_date)
    if end < start:
        return None
    holidays = set(
        (await db.execute(select(Holiday.date).where(Holiday.date >= start, Holiday.date <= end))).scalars()
    )
    working = {start + timedelta(days=i) for i in range((end - start).days + 1)}
    working = {d for d in working if d.weekday() != 6 and d not in holidays}
    leave_days: set[date] = set()
    for lf, lt in (
        await db.execute(
            select(LeaveRequest.from_date, LeaveRequest.to_date).where(
                LeaveRequest.employee_id == emp.id,
                LeaveRequest.status == "approved",
                LeaveRequest.from_date <= end,
                LeaveRequest.to_date >= start,
            )
        )
    ).all():
        d = max(lf, start)
        while d <= min(lt, end):
            leave_days.add(d)
            d += timedelta(days=1)
    expected = working - leave_days
    if not expected:
        return None
    present = Decimal(0)
    for d, status in (
        await db.execute(
            select(Attendance.date, Attendance.status).where(
                Attendance.employee_id == emp.id,
                Attendance.date >= start,
                Attendance.date <= end,
            )
        )
    ).all():
        if d in expected:
            present += {"present": 1, "wfh": 1, "half_day": Decimal("0.5")}.get(status, 0)
    return round(float(present) / len(expected) * 100, 1)


async def check_eligibility(
    db: AsyncSession,
    scheme: IncentiveScheme,
    emp: Employee,
    start: date,
    end: date,
    att: Optional[float],
) -> list[str]:
    """Reasons the employee does not qualify (empty = eligible)."""
    reasons: list[str] = []
    if emp.status in LEFT:
        reasons.append("Has left the company")
    if scheme.confirmed_only and emp.is_on_probation:
        reasons.append("Still on probation")
    if scheme.min_tenure_days and emp.date_of_joining:
        days = (end - emp.date_of_joining).days + 1
        if days < scheme.min_tenure_days:
            reasons.append(f"Joined {days} days before the period ended (needs {scheme.min_tenure_days})")
    if scheme.min_attendance_pct is not None:
        if att is None:
            reasons.append("No working days to check attendance")
        elif att < scheme.min_attendance_pct:
            reasons.append(f"Attendance {att:.0f}% (needs {scheme.min_attendance_pct}%)")
    if scheme.exclude_notice:
        notice = (
            await db.execute(
                select(Resignation.id).where(
                    Resignation.employee_id == emp.id,
                    Resignation.status.in_(NOTICE_STATES),
                ).limit(1)
            )
        ).first()
        if notice or emp.status in ("resigned", "terminated"):
            reasons.append("Serving notice / leaving")
    if scheme.no_warning_days:
        since = end - timedelta(days=scheme.no_warning_days)
        warned = (
            await db.execute(
                select(EmployeeLetter.issued_on).where(
                    EmployeeLetter.employee_id == emp.id,
                    EmployeeLetter.letter_type == "warning",
                    EmployeeLetter.is_removed.is_(False),
                    EmployeeLetter.issued_on >= since,
                    EmployeeLetter.issued_on <= end,
                ).limit(1)
            )
        ).first()
        if warned:
            reasons.append(f"Warning letter in the last {scheme.no_warning_days} days")
    return reasons


async def _target_for(
    db: AsyncSession, emp_id: int, metric: str, start: date, end: date
) -> Optional[SalesTarget]:
    """The employee's target of this kind for the period: the one with
    the same dates, else the one overlapping the period most."""
    rows = (
        await db.execute(
            select(SalesTarget).where(
                SalesTarget.employee_id == emp_id,
                SalesTarget.metric == metric,
                SalesTarget.period_start <= end,
                SalesTarget.period_end >= start,
            )
        )
    ).scalars().all()
    if not rows:
        return None

    def overlap(t: SalesTarget) -> int:
        return (min(t.period_end, end) - max(t.period_start, start)).days

    exact = [t for t in rows if t.period_start == start and t.period_end == end]
    return exact[0] if exact else max(rows, key=overlap)


async def _categories(db: AsyncSession) -> dict[int, str]:
    return dict((await db.execute(select(EmployeeCategory.id, EmployeeCategory.code))).all())


async def covered_employees(db: AsyncSession, scheme: IncentiveScheme) -> list[Employee]:
    cats = await _categories(db)
    staff = (
        await db.execute(select(Employee).where(Employee.status.not_in(("separated", "inactive"))))
    ).unique().scalars().all()
    return [e for e in staff if applies_to(scheme, e, cats.get(e.category_id))]


# ── Runs ─────────────────────────────────────────────────────────────
async def get_scheme(db: AsyncSession, scheme_id: int) -> IncentiveScheme:
    s = (await db.execute(select(IncentiveScheme).where(IncentiveScheme.id == scheme_id))).scalar_one_or_none()
    if not s:
        raise NotFoundError("Scheme not found")
    return s


async def get_run(db: AsyncSession, run_id: int) -> IncentiveRun:
    r = (await db.execute(select(IncentiveRun).where(IncentiveRun.id == run_id))).scalar_one_or_none()
    if not r:
        raise NotFoundError("Incentive run not found")
    return r


async def calculate_run(
    db: AsyncSession,
    scheme: IncentiveScheme,
    *,
    period_start: date,
    payout: Optional[tuple[int, int]] = None,
    actor: Optional[User] = None,
    notify: bool = True,
) -> IncentiveRun:
    """Create (or recalculate) the run for the period containing
    ``period_start``. Lines a manager has already reviewed keep their
    decision; their figures are refreshed."""
    from app.services.sales_service import recompute_target_achievement

    start, end = period_for(scheme.period_type, period_start)
    run = (
        await db.execute(
            select(IncentiveRun).where(
                IncentiveRun.scheme_id == scheme.id, IncentiveRun.period_start == start
            )
        )
    ).scalar_one_or_none()
    if run and run.status != "review":
        raise ConflictError("This run is already approved — reopen it to recalculate")
    if not run:
        py, pm = payout or (end.year, end.month)
        run = IncentiveRun(
            scheme_id=scheme.id, period_start=start, period_end=end,
            payout_year=py, payout_month=pm, status="review",
            created_by=actor.id if actor else None,
        )
        db.add(run)
        await db.flush()
    elif payout:
        run.payout_year, run.payout_month = payout

    existing = {
        ln.employee_id: ln
        for ln in (await db.execute(select(IncentiveLine).where(IncentiveLine.run_id == run.id))).scalars()
    }
    seen: set[int] = set()
    for emp in await covered_employees(db, scheme):
        target = await _target_for(db, emp.id, scheme.metric, start, end)
        if target is None:
            continue
        target = await recompute_target_achievement(db, target.id)
        pct = float(target.achieved_amount / target.target_amount * 100) if target.target_amount else 0.0
        att = await attendance_pct(db, emp, start, end)
        reasons = await check_eligibility(db, scheme, emp, start, end, att)
        slab = slab_reached(scheme, pct)
        calc = payout_for(scheme, slab, target.achieved_amount)
        if slab is None:
            lowest = (scheme.slabs or [{}])[0].get("min_pct")
            reasons.append(f"Below the first slab ({lowest:g}%)" if lowest else "No slab reached")
        eligible = not reasons
        ln = existing.get(emp.id) or IncentiveLine(run_id=run.id, employee_id=emp.id)
        ln.target_id = target.id
        ln.target_amount = target.target_amount
        ln.achieved_amount = target.achieved_amount
        ln.achievement_pct = Decimal(str(round(pct, 2)))
        ln.slab_min_pct = Decimal(str(slab["min_pct"])) if slab else None
        ln.attendance_pct = Decimal(str(att)) if att is not None else None
        ln.eligible = eligible
        ln.reasons = reasons
        ln.calculated_amount = calc
        if ln.review_status == "pending" or ln.id is None:
            ln.review_status = "pending"
            ln.amount = calc if eligible else Decimal(0)
        if ln.id is None:
            db.add(ln)
        seen.add(emp.id)
    # People no longer covered (target removed …) drop out if unreviewed.
    for emp_id, ln in existing.items():
        if emp_id not in seen and ln.review_status == "pending":
            await db.delete(ln)
    await db.commit()
    await db.refresh(run)
    if notify:
        await _ask_managers(db, run, scheme)
    return run


async def _notify(db: AsyncSession, user_id: Optional[int], *, type: str, title: str, body: str, data: dict) -> None:
    if not user_id:
        return
    from app.services.notification_service import notify

    try:
        await notify(db, user_id=user_id, type=type, title=title, body=body, data=data, send_push=True)
    except Exception:  # pragma: no cover
        await db.rollback()


def _period_label(run: IncentiveRun) -> str:
    if run.period_start.month == run.period_end.month:
        return run.period_start.strftime("%b %Y")
    return f"{run.period_start.strftime('%b')}–{run.period_end.strftime('%b %Y')}"


async def _ask_managers(db: AsyncSession, run: IncentiveRun, scheme: IncentiveScheme) -> None:
    """Tell each direct manager how many of their people need a review."""
    rows = (
        await db.execute(
            select(Employee.reporting_to, func.count())
            .join(IncentiveLine, IncentiveLine.employee_id == Employee.id)
            .where(IncentiveLine.run_id == run.id, IncentiveLine.review_status == "pending")
            .group_by(Employee.reporting_to)
        )
    ).all()
    for mgr_id, n in rows:
        if not mgr_id:
            continue
        mgr = (await db.execute(select(Employee).where(Employee.id == mgr_id))).scalar_one_or_none()
        if mgr and mgr.user_id:
            await _notify(
                db, mgr.user_id,
                type="incentive_review",
                title=f"Review incentives: {scheme.name} · {_period_label(run)}",
                body=f"{n} {'person' if n == 1 else 'people'} in your team to approve.",
                data={"run_id": run.id},
            )


# ── Review & approval ────────────────────────────────────────────────
async def reviewable_ids(db: AsyncSession, user: User) -> Optional[set[int]]:
    """Whose lines the user may review: everyone for HR / payroll, else
    their direct reports (pay is sensitive — skip-levels don't)."""
    if can_manage(user):
        return None
    me = await emp_svc.get_self_employee(db, user)
    if not me:
        return set()
    return await emp_svc.subordinate_ids(db, me.id, depth=1)


async def review_line(
    db: AsyncSession, user: User, line_id: int, *, action: str, amount=None, note: Optional[str] = None
) -> IncentiveLine:
    ln = (await db.execute(select(IncentiveLine).where(IncentiveLine.id == line_id))).scalar_one_or_none()
    if not ln:
        raise NotFoundError("Line not found")
    allowed = await reviewable_ids(db, user)
    if allowed is not None and ln.employee_id not in allowed:
        raise NotFoundError("Line not found")
    run = await get_run(db, ln.run_id)
    if run.status != "review":
        raise ConflictError("This run has already been approved")
    if action == "approve":
        ln.review_status = "approved"
        ln.amount = ln.calculated_amount if ln.eligible else Decimal(0)
    elif action == "adjust":
        if amount is None or Decimal(str(amount)) < 0:
            raise ValidationError("Enter the amount to pay")
        if not (note or "").strip():
            raise ValidationError("Say why the amount was changed")
        ln.review_status = "adjusted"
        ln.amount = _money(amount)
    elif action == "reject":
        if not (note or "").strip():
            raise ValidationError("Say why it was rejected")
        ln.review_status = "rejected"
        ln.amount = Decimal(0)
    elif action == "reset":
        ln.review_status = "pending"
        ln.amount = ln.calculated_amount if ln.eligible else Decimal(0)
    else:
        raise ValidationError("Unknown action")
    ln.review_note = (note or "").strip()[:500] or None
    ln.reviewed_by = user.id
    ln.reviewed_at = _now()
    await db.commit()
    await db.refresh(ln)
    return ln


async def approve_run(db: AsyncSession, user: User, run_id: int, *, approve_pending: bool) -> IncentiveRun:
    run = await get_run(db, run_id)
    if run.status != "review":
        raise ConflictError("Only runs under review can be approved")
    lines = (await db.execute(select(IncentiveLine).where(IncentiveLine.run_id == run.id))).scalars().all()
    pending = [ln for ln in lines if ln.review_status == "pending"]
    if pending and not approve_pending:
        raise ConflictError(f"{len(pending)} line(s) still waiting for the manager's review")
    for ln in pending:
        ln.review_status = "approved"
        ln.amount = ln.calculated_amount if ln.eligible else Decimal(0)
        ln.reviewed_by = user.id
        ln.reviewed_at = _now()
        ln.review_note = "Approved by HR"
    run.status = "approved"
    run.approved_by = user.id
    run.approved_at = _now()
    await db.commit()
    await db.refresh(run)
    scheme = await get_scheme(db, run.scheme_id)
    payday = date(run.payout_year, run.payout_month, 1).strftime("%B %Y")
    people = {
        e.id: e
        for e in (
            await db.execute(select(Employee).where(Employee.id.in_([ln.employee_id for ln in lines] or [-1])))
        ).unique().scalars()
    }
    for ln in lines:
        if ln.amount and ln.amount > 0:
            await _notify(
                db, people[ln.employee_id].user_id,
                type="incentive_approved",
                title=f"Incentive approved: ₹{int(ln.amount):,}",
                body=f"{scheme.name} · {_period_label(run)}. Paid with your {payday} salary.",
                data={"run_id": run.id},
            )
    return run


async def reopen_run(db: AsyncSession, run_id: int) -> IncentiveRun:
    run = await get_run(db, run_id)
    paid = (
        await db.execute(
            select(IncentiveLine.id).where(
                IncentiveLine.run_id == run.id, IncentiveLine.paid_in_run_id.is_not(None)
            ).limit(1)
        )
    ).first()
    if paid:
        raise ConflictError("Already included in a payroll run — revert that payroll first")
    run.status = "review"
    run.approved_by = None
    run.approved_at = None
    await db.commit()
    await db.refresh(run)
    return run


# ── Payroll ──────────────────────────────────────────────────────────
async def payable_lines(db: AsyncSession, employee_id: int, run: PayrollRun) -> list[IncentiveLine]:
    """Approved incentives due in this payroll month and not already
    paid by another payroll run."""
    return list(
        (
            await db.execute(
                select(IncentiveLine)
                .join(IncentiveRun, IncentiveRun.id == IncentiveLine.run_id)
                .where(
                    IncentiveLine.employee_id == employee_id,
                    IncentiveRun.status == "approved",
                    IncentiveRun.payout_year == run.year,
                    IncentiveRun.payout_month == run.month,
                    IncentiveLine.review_status.in_(("approved", "adjusted")),
                    IncentiveLine.amount > 0,
                    or_(IncentiveLine.paid_in_run_id.is_(None), IncentiveLine.paid_in_run_id == run.id),
                )
            )
        ).scalars()
    )


# ── Views ────────────────────────────────────────────────────────────
async def run_summary(db: AsyncSession, run: IncentiveRun) -> dict:
    stats = (
        await db.execute(
            select(
                func.count(),
                func.sum(IncentiveLine.eligible.cast(Integer)),
                func.coalesce(func.sum(IncentiveLine.amount), 0),
            ).where(IncentiveLine.run_id == run.id)
        )
    ).one()
    pending = (
        await db.execute(
            select(func.count()).where(
                IncentiveLine.run_id == run.id, IncentiveLine.review_status == "pending"
            )
        )
    ).scalar()
    paid = (
        await db.execute(
            select(func.count()).where(
                IncentiveLine.run_id == run.id, IncentiveLine.paid_in_run_id.is_not(None)
            )
        )
    ).scalar()
    scheme = await get_scheme(db, run.scheme_id)
    return {
        "id": run.id,
        "scheme_id": run.scheme_id,
        "scheme_name": scheme.name,
        "metric": scheme.metric,
        "period_start": run.period_start,
        "period_end": run.period_end,
        "period_label": _period_label(run),
        "payout_year": run.payout_year,
        "payout_month": run.payout_month,
        "status": run.status,
        "lines": stats[0] or 0,
        "eligible": int(stats[1] or 0),
        "pending_review": pending or 0,
        "paid_lines": paid or 0,
        "total_amount": Decimal(str(stats[2] or 0)),
        "approved_at": run.approved_at,
    }


async def serialize_lines(db: AsyncSession, lines: Iterable[IncentiveLine]) -> list[dict]:
    lines = list(lines)
    people = {
        e.id: e
        for e in (
            await db.execute(select(Employee).where(Employee.id.in_([ln.employee_id for ln in lines] or [-1])))
        ).unique().scalars()
    }
    managers = {
        e.id: e
        for e in (
            await db.execute(
                select(Employee).where(
                    Employee.id.in_([p.reporting_to for p in people.values() if p.reporting_to] or [-1])
                )
            )
        ).unique().scalars()
    }
    runs = {
        r.id: r
        for r in (
            await db.execute(select(IncentiveRun).where(IncentiveRun.id.in_({ln.run_id for ln in lines} or {-1})))
        ).scalars()
    }
    schemes = {
        s.id: s
        for s in (
            await db.execute(
                select(IncentiveScheme).where(IncentiveScheme.id.in_({r.scheme_id for r in runs.values()} or {-1}))
            )
        ).scalars()
    }
    paid_runs = {
        r.id: r
        for r in (
            await db.execute(
                select(PayrollRun).where(PayrollRun.id.in_({ln.paid_in_run_id for ln in lines if ln.paid_in_run_id} or {-1}))
            )
        ).scalars()
    }
    out = []
    for ln in lines:
        e = people.get(ln.employee_id)
        run = runs.get(ln.run_id)
        scheme = schemes.get(run.scheme_id) if run else None
        pr = paid_runs.get(ln.paid_in_run_id) if ln.paid_in_run_id else None
        out.append(
            {
                "id": ln.id,
                "run_id": ln.run_id,
                "scheme_name": scheme.name if scheme else None,
                "metric": scheme.metric if scheme else None,
                "period_label": _period_label(run) if run else None,
                "run_status": run.status if run else None,
                "employee_id": ln.employee_id,
                "employee_name": _name(e),
                "employee_code": e.employee_code if e else None,
                "designation": e.designation.name if e and e.designation else None,
                "manager_name": _name(managers.get(e.reporting_to)) if e and e.reporting_to else None,
                "target_amount": ln.target_amount,
                "achieved_amount": ln.achieved_amount,
                "achievement_pct": float(ln.achievement_pct or 0),
                "slab_min_pct": float(ln.slab_min_pct) if ln.slab_min_pct is not None else None,
                "attendance_pct": float(ln.attendance_pct) if ln.attendance_pct is not None else None,
                "eligible": ln.eligible,
                "reasons": ln.reasons or [],
                "calculated_amount": ln.calculated_amount,
                "amount": ln.amount,
                "review_status": ln.review_status,
                "review_note": ln.review_note,
                "reviewed_at": ln.reviewed_at,
                "paid": bool(pr and pr.disbursed),
                "in_payroll": ln.paid_in_run_id is not None,
                "payout_label": date(run.payout_year, run.payout_month, 1).strftime("%B %Y") if run else None,
            }
        )
    return out


async def my_incentives(db: AsyncSession, emp: Employee) -> dict:
    """What the employee can earn this period, and what they've earned."""
    today = date.today()
    cats = await _categories(db)
    schemes = (
        await db.execute(select(IncentiveScheme).where(IncentiveScheme.is_active.is_(True)))
    ).scalars().all()
    current = []
    for s in schemes:
        if not applies_to(s, emp, cats.get(emp.category_id)):
            continue
        start, end = period_for(s.period_type, today)
        t = await _target_for(db, emp.id, s.metric, start, end)
        if not t:
            continue
        pct = float(t.achieved_amount / t.target_amount * 100) if t.target_amount else 0.0
        reached = slab_reached(s, pct)
        nxt = next_slab(s, pct)
        att = await attendance_pct(db, emp, start, end)
        warnings = [
            r for r in await check_eligibility(db, s, emp, start, end, att)
            if not r.startswith("Below the first slab")
        ]
        gap = None
        if nxt and t.target_amount:
            gap = _money(Decimal(str(nxt["min_pct"])) / 100 * t.target_amount - t.achieved_amount)
        current.append(
            {
                "scheme_id": s.id,
                "scheme_name": s.name,
                "description": s.description,
                "metric": s.metric,
                "unit": METRIC_UNITS.get(s.metric, ""),
                "period_start": start,
                "period_end": end,
                "target_amount": t.target_amount,
                "achieved_amount": t.achieved_amount,
                "achievement_pct": round(pct, 1),
                "slabs": [
                    {**sl, "amount": payout_for(s, sl, t.achieved_amount if s.payout_type == "fixed"
                                                else Decimal(str(sl["min_pct"])) / 100 * t.target_amount)}
                    for sl in s.slabs or []
                ],
                "earning_now": payout_for(s, reached, t.achieved_amount),
                "next_slab": (
                    {
                        "min_pct": nxt["min_pct"],
                        "amount": payout_for(
                            s, nxt,
                            Decimal(str(nxt["min_pct"])) / 100 * t.target_amount,
                        ),
                        "still_needed": gap,
                    }
                    if nxt
                    else None
                ),
                "attendance_pct": att,
                "warnings": warnings,
            }
        )
    history_lines = (
        await db.execute(
            select(IncentiveLine)
            .join(IncentiveRun, IncentiveRun.id == IncentiveLine.run_id)
            .where(IncentiveLine.employee_id == emp.id, IncentiveRun.status != "cancelled")
            .order_by(IncentiveRun.period_start.desc())
            .limit(24)
        )
    ).scalars().all()
    history = await serialize_lines(db, history_lines)
    # Employees don't see review notes until HR has approved.
    for h in history:
        if h["run_status"] != "approved":
            h["amount"] = None
            h["review_note"] = None
    return {"current": current, "history": history}


# ── Monthly job ──────────────────────────────────────────────────────
async def auto_calculate(db: AsyncSession, today: Optional[date] = None) -> dict:
    """At the start of a period, calculate the one that just ended for
    every active scheme (once)."""
    today = today or date.today()
    made = 0
    for s in (await db.execute(select(IncentiveScheme).where(IncentiveScheme.is_active.is_(True)))).scalars():
        start, _ = previous_period(s.period_type, today)
        cur_start, _ = period_for(s.period_type, today)
        if (today - cur_start).days > 6:
            continue  # only in the first week of a new period
        exists = (
            await db.execute(
                select(IncentiveRun.id).where(
                    IncentiveRun.scheme_id == s.id, IncentiveRun.period_start == start
                )
            )
        ).first()
        if exists:
            continue
        await calculate_run(db, s, period_start=start)
        made += 1
    return {"runs_created": made}


def validate_scheme(payload: dict) -> dict:
    out = dict(payload)
    if "metric" in out and out["metric"] not in TARGET_METRICS:
        raise ValidationError("Unknown target type")
    if "payout_type" in out and out["payout_type"] not in PAYOUT_TYPES:
        raise ValidationError("Unknown payout type")
    if "period_type" in out and out["period_type"] not in ("monthly", "quarterly"):
        raise ValidationError("Period must be monthly or quarterly")
    if "slabs" in out:
        out["slabs"] = clean_slabs(out["slabs"])
    if out.get("payout_type") == "percent_of_achieved" and out.get("metric", "sales_amount") != "sales_amount":
        raise ValidationError("A % payout only works for sales (₹) targets")
    for k in ("min_attendance_pct",):
        if out.get(k) is not None and not (0 <= int(out[k]) <= 100):
            raise ValidationError("Attendance % must be 0–100")
    return out


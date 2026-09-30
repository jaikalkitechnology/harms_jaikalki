"""PF wage ceiling register.

Two lookups:
- ``cap_on(date)`` — cap in force on a single date. Used for CTC
  packages, template previews, offer letters and salary revisions.
- ``caps_for_wage_month(year, month)`` — the cap for a payroll month,
  day-weighted across the calendar days of the wage month. A change
  effective 17 Sep gives September = 15,000 x 16/30 + 25,000 x 14/30.
  The attendance cycle window plays no part here: PF is computed on the
  wage month.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import PayrollRun, PfWageCeiling, User

# Statutory ceiling in force before any register entry (EPFO, 1 Sep 2014).
BASELINE_CAP = Decimal("15000")
BASELINE_FROM = date(2014, 9, 1)

MODES = ("day_weighted", "whole_month", "next_month")


def applies_from(rec: PfWageCeiling) -> date:
    """First date the record's cap counts, after mid-month handling."""
    eff = rec.effective_from
    if eff.day == 1 or rec.mid_month_mode == "day_weighted":
        return eff
    if rec.mid_month_mode == "whole_month":
        return eff.replace(day=1)
    # next_month
    return (eff.replace(day=1) + timedelta(days=32)).replace(day=1)


async def ensure_seed(db: AsyncSession) -> None:
    """Make sure the register has the statutory baseline row."""
    exists = (
        await db.execute(select(PfWageCeiling.id).limit(1))
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            PfWageCeiling(
                cap_amount=BASELINE_CAP,
                eps_cap_amount=BASELINE_CAP,
                edli_cap_amount=BASELINE_CAP,
                effective_from=BASELINE_FROM,
                recorded_on=BASELINE_FROM,
                mid_month_mode="day_weighted",
                reference="EPFO statutory ceiling",
            )
        )
        await db.commit()


async def list_ceilings(db: AsyncSession) -> Sequence[PfWageCeiling]:
    await ensure_seed(db)
    return (
        await db.execute(
            select(PfWageCeiling).order_by(
                PfWageCeiling.effective_from, PfWageCeiling.id
            )
        )
    ).scalars().all()


def _pick_all(
    records: Sequence[PfWageCeiling], d: date
) -> tuple[Decimal, Decimal, Decimal]:
    """(pf_cap, eps_cap, edli_cap) in force on ``d``."""
    best: Optional[PfWageCeiling] = None
    best_from: Optional[date] = None
    for r in records:
        start = applies_from(r)
        if start <= d and (
            best_from is None
            or start > best_from
            or (start == best_from and r.id > best.id)  # type: ignore[union-attr]
        ):
            best, best_from = r, start
    if best is None:
        return BASELINE_CAP, BASELINE_CAP, BASELINE_CAP
    return (
        Decimal(best.cap_amount),
        Decimal(best.eps_cap_amount),
        Decimal(best.edli_cap_amount or BASELINE_CAP),
    )


def _pick(records: Sequence[PfWageCeiling], d: date) -> tuple[Decimal, Decimal]:
    pf, eps, _edli = _pick_all(records, d)
    return pf, eps


async def cap_on(db: AsyncSession, d: date) -> tuple[Decimal, Decimal]:
    """(pf_cap, eps_cap) in force on date ``d``."""
    return _pick(await list_ceilings(db), d)


def weighted_caps(
    records: Sequence[PfWageCeiling], year: int, month: int
) -> tuple[Decimal, Decimal]:
    days = monthrange(year, month)[1]
    pf_total = Decimal(0)
    eps_total = Decimal(0)
    for day in range(1, days + 1):
        pf, eps = _pick(records, date(year, month, day))
        pf_total += pf
        eps_total += eps
    q = Decimal("0.01")
    return (pf_total / days).quantize(q), (eps_total / days).quantize(q)


def weighted_ceilings(
    records: Sequence[PfWageCeiling], year: int, month: int
) -> dict[str, Decimal]:
    """Day-weighted PF / EPS / EDLI ceilings for a wage month."""
    days = monthrange(year, month)[1]
    totals = [Decimal(0), Decimal(0), Decimal(0)]
    for day in range(1, days + 1):
        for i, v in enumerate(_pick_all(records, date(year, month, day))):
            totals[i] += v
    q = Decimal("0.01")
    pf, eps, edli = ((t / days).quantize(q) for t in totals)
    return {"pf": pf, "eps": eps, "edli": edli}


async def ceilings_for_wage_month(
    db: AsyncSession, year: int, month: int
) -> dict[str, Decimal]:
    return weighted_ceilings(await list_ceilings(db), year, month)


async def caps_for_wage_month(
    db: AsyncSession, year: int, month: int
) -> tuple[Decimal, Decimal]:
    """(pf_cap, eps_cap) for a payroll/wage month, day-weighted."""
    return weighted_caps(await list_ceilings(db), year, month)


# ── Editing guard ─────────────────────────────────────────────────────
async def _locked_by_payroll(db: AsyncSession, start: date) -> bool:
    """True if a finalized / disbursed payroll covers a wage month that
    a cap starting on ``start`` would change."""
    runs = (
        await db.execute(
            select(PayrollRun).where(
                (PayrollRun.status == "finalized") | (PayrollRun.disbursed.is_(True))
            )
        )
    ).scalars().all()
    for r in runs:
        month_end = date(r.year, r.month, monthrange(r.year, r.month)[1])
        if month_end >= start:
            return True
    return False


def _validate(payload: dict) -> None:
    cap = payload.get("cap_amount")
    if cap is not None and Decimal(cap) <= 0:
        raise ValidationError("Cap must be greater than zero")
    eps = payload.get("eps_cap_amount")
    if eps is not None and Decimal(eps) <= 0:
        raise ValidationError("EPS cap must be greater than zero")
    edli = payload.get("edli_cap_amount")
    if edli is not None and Decimal(edli) <= 0:
        raise ValidationError("EDLI cap must be greater than zero")
    mode = payload.get("mid_month_mode")
    if mode is not None and mode not in MODES:
        raise ValidationError(f"mid_month_mode must be one of {', '.join(MODES)}")


async def get(db: AsyncSession, ceiling_id: int) -> PfWageCeiling:
    rec = (
        await db.execute(select(PfWageCeiling).where(PfWageCeiling.id == ceiling_id))
    ).scalar_one_or_none()
    if rec is None:
        raise NotFoundError("PF ceiling record not found")
    return rec


async def create(
    db: AsyncSession, payload: dict, *, actor: Optional[User] = None
) -> PfWageCeiling:
    _validate(payload)
    rec = PfWageCeiling(
        cap_amount=Decimal(payload["cap_amount"]),
        eps_cap_amount=Decimal(
            payload.get("eps_cap_amount") or BASELINE_CAP
        ),
        edli_cap_amount=Decimal(
            payload.get("edli_cap_amount") or BASELINE_CAP
        ),
        effective_from=payload["effective_from"],
        recorded_on=payload.get("recorded_on") or date.today(),
        mid_month_mode=payload.get("mid_month_mode") or "day_weighted",
        reference=payload.get("reference"),
        notes=payload.get("notes"),
        created_by=actor.id if actor else None,
    )
    if await _locked_by_payroll(db, applies_from(rec)):
        raise ValidationError(
            "A finalized or disbursed payroll already covers that date. "
            "Choose a later effective date, or revert that payroll first."
        )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def update(db: AsyncSession, ceiling_id: int, payload: dict) -> PfWageCeiling:
    _validate(payload)
    rec = await get(db, ceiling_id)
    if await _locked_by_payroll(db, applies_from(rec)):
        raise ValidationError(
            "This record was used by a finalized or disbursed payroll and "
            "can't be changed. Add a new record instead."
        )
    for key in (
        "cap_amount",
        "eps_cap_amount",
        "edli_cap_amount",
        "effective_from",
        "recorded_on",
        "mid_month_mode",
        "reference",
        "notes",
    ):
        if key in payload and payload[key] is not None:
            setattr(rec, key, payload[key])
    if await _locked_by_payroll(db, applies_from(rec)):
        await db.rollback()
        raise ValidationError(
            "A finalized or disbursed payroll already covers the new date."
        )
    await db.commit()
    await db.refresh(rec)
    return rec


async def delete(db: AsyncSession, ceiling_id: int) -> None:
    rec = await get(db, ceiling_id)
    if await _locked_by_payroll(db, applies_from(rec)):
        raise ValidationError(
            "This record was used by a finalized or disbursed payroll and "
            "can't be deleted."
        )
    total = len(await list_ceilings(db))
    if total <= 1:
        raise ValidationError("At least one PF ceiling record must remain.")
    await db.delete(rec)
    await db.commit()


# ── Impact preview + absorb as salary revision ────────────────────────
def _first_full_month(rec: PfWageCeiling) -> date:
    start = applies_from(rec)
    if start.day == 1:
        return start
    return (start.replace(day=1) + timedelta(days=32)).replace(day=1)


async def _affected(db: AsyncSession, rec: PfWageCeiling):
    """Yield (employee, template, old_breakup, new_breakup) for everyone
    whose PF changes under this record's cap."""
    from app.models import Employee, SalaryTemplate
    from app.services.salary_calculator import JaikalkiSalaryCalculator

    records = await list_ceilings(db)
    others = [r for r in records if r.id != rec.id]
    old_cap, _ = _pick(others, applies_from(rec))
    new_cap = Decimal(rec.cap_amount)

    emps = (
        await db.execute(select(Employee).where(Employee.status == "active"))
    ).scalars().all()
    templates = {
        t.id: t
        for t in (await db.execute(select(SalaryTemplate))).scalars().all()
    }
    calc = JaikalkiSalaryCalculator()
    for e in emps:
        t = templates.get(e.salary_template_id) if e.salary_template_id else None
        if t is None or t.category == "intern":
            continue
        if getattr(e, "pf_opt_out", False) or getattr(e, "pf_basic_cap_override", None):
            continue  # opted out, or has an individual cap
        old = calc.calculate(t, ctc_annual=e.ctc_annual or None, employee=e, pf_cap=old_cap)
        new = calc.calculate(t, ctc_annual=e.ctc_annual or None, employee=e, pf_cap=new_cap)
        if old.pf_employer == new.pf_employer and old.pf_employee == new.pf_employee:
            continue
        yield e, t, old, new, old_cap, new_cap


def _absorb_ctc(calc, template, emp, target_gross: int, start_ctc: Decimal, cap: Decimal) -> int:
    """Smallest CTC (annual, whole rupees) that keeps gross at ``target_gross``
    under the new cap."""
    ctc = Decimal(start_ctc)
    for _ in range(8):
        br = calc.calculate(template, ctc_annual=ctc, employee=emp, pf_cap=cap)
        gap = target_gross - br.gross
        if gap == 0:
            break
        ctc += Decimal(gap) * 12
    return int(ctc)


async def impact(db: AsyncSession, ceiling_id: int) -> dict:
    from app.services.salary_calculator import JaikalkiSalaryCalculator

    rec = await get(db, ceiling_id)
    calc = JaikalkiSalaryCalculator()
    rows = []
    records_all = await list_ceilings(db)
    old_cap, _ = _pick([r for r in records_all if r.id != rec.id], applies_from(rec))
    new_cap = Decimal(rec.cap_amount)
    async for e, t, old, new, _oc, _nc in _affected(db, rec):
        base_ctc = Decimal(e.ctc_annual or 0) or Decimal(old.total_ctc_annual)
        extra_er = (new.pf_employer - old.pf_employer) * 12
        rows.append(
            {
                "employee_id": e.id,
                "employee_code": e.employee_code,
                "name": f"{e.first_name} {e.last_name}".strip(),
                "basic": old.basic,
                "old_pf_employee": old.pf_employee,
                "new_pf_employee": new.pf_employee,
                "old_pf_employer": old.pf_employer,
                "new_pf_employer": new.pf_employer,
                "old_gross": old.gross,
                "new_gross": new.gross,
                "old_net": old.net_salary,
                "new_net": new.net_salary,
                "net_change": new.net_salary - old.net_salary,
                "absorb_ctc_annual": _absorb_ctc(
                    calc, t, e, old.gross, base_ctc + extra_er, new_cap
                ),
            }
        )
    rows.sort(key=lambda r: r["net_change"])
    first_full = _first_full_month(rec)
    records = await list_ceilings(db)
    eff = rec.effective_from
    return {
        "ceiling_id": rec.id,
        "old_cap": old_cap,
        "new_cap": new_cap,
        "first_full_month": f"{first_full.year}-{first_full.month:02d}",
        "effective_month_cap": weighted_caps(records, eff.year, eff.month)[0],
        "rows": rows,
    }


async def absorb(
    db: AsyncSession,
    ceiling_id: int,
    *,
    employee_ids: list[int],
    effective_date: Optional[date],
    reason: str,
    actor: User,
) -> dict:
    """Create salary revisions (pending approval) that raise CTC so each
    selected employee's gross stays the same under the new cap.

    Each revision is committed on its own, so one failure never blocks
    the rest. Everything the loop needs is captured as plain values up
    front: a rollback expires loaded ORM objects, and touching an
    expired object in async code raises MissingGreenlet.
    """
    from app.models import Employee, SalaryRevision
    from app.services import compensation_service

    rec = await get(db, ceiling_id)
    eff = effective_date or rec.effective_from
    actor_id = actor.id
    preview = {r["employee_id"]: r for r in (await impact(db, ceiling_id))["rows"]}

    open_ids = set(
        (
            await db.execute(
                select(SalaryRevision.employee_id).where(
                    SalaryRevision.employee_id.in_(employee_ids),
                    SalaryRevision.status.in_(("draft", "pending_approval", "approved")),
                )
            )
        ).scalars().all()
    )

    created: list[dict] = []
    skipped: list[dict] = []
    for emp_id in employee_ids:
        row = preview.get(emp_id)
        if row is None:
            skipped.append({"employee_id": emp_id, "reason": "Not affected by this cap"})
            continue
        if emp_id in open_ids:
            skipped.append({
                "employee_id": emp_id,
                "reason": f"{row['name']} already has an open salary revision",
            })
            continue
        proposer = await db.get(User, actor_id)
        try:
            rev = await compensation_service.propose(
                db,
                proposer=proposer,
                employee_id=emp_id,
                new_ctc_annual=row["absorb_ctc_annual"],
                effective_date=eff,
                reason="other",
                notes=reason,
            )
            created.append({
                "employee_id": emp_id,
                "revision_id": rev.id,
                "new_ctc_annual": row["absorb_ctc_annual"],
            })
        except Exception as exc:
            await db.rollback()
            detail = getattr(exc, "detail", None)
            if not isinstance(detail, str) or not detail.strip():
                detail = f"{exc.__class__.__name__}: {str(exc).splitlines()[0][:160]}"
            skipped.append({"employee_id": emp_id, "reason": f"{row['name']}: {detail}"})
    return {"created": created, "skipped": skipped}

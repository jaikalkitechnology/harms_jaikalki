"""Payroll engine: bulk-process monthly payroll, generate payslips."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Employee,
    PayrollRun,
    Payslip,
    Reimbursement,
    User,
)
from app.services.leave_policy import get_leave_policy
from app.services.payroll_attendance import compute_attendance_month, cycle_window
from app.services.salary_calculator import JaikalkiSalaryCalculator


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _earned_statutory(
    breakup: dict,
    scaling: Decimal,
    earned_gross: Decimal,
    emp: Employee,
    pf_cap: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """PF / ESIC / PT on what was actually earned this month.

    Eligibility comes from the monthly breakup (opt-outs, ESIC ceiling
    on contractual gross). Amounts are recomputed on earned pay so a
    part month is never charged full-month deductions.
    ``pf_cap`` is the wage-month cap from the PF ceiling register; an
    employee's own pf_basic_cap_override wins.
    Returns (pf_employee, pf_employer, esic_employee, esic_employer, pt,
    pf_wages).
    """
    from app.services.salary_calculator import (
        ESIC_EMPLOYEE_RATE,
        ESIC_EMPLOYER_RATE,
        PF_EMPLOYEE_RATE,
        PF_EMPLOYER_RATE,
        _pt_slab,
        _round,
    )

    zero = Decimal("0")
    if earned_gross <= 0:
        return zero, zero, zero, zero, zero, zero

    if Decimal(breakup.get("pf_employee") or 0) > 0:
        cap = Decimal(getattr(emp, "pf_basic_cap_override", None) or pf_cap)
        # Round PF wages to whole rupees first and derive contributions
        # from that figure — the EPFO portal checks employee share ==
        # round(12% x EPF wages) on every ECR row.
        pf_wages = Decimal(_round(min(Decimal(breakup["basic"]) * scaling, cap)))
        pf_emp = Decimal(_round(pf_wages * PF_EMPLOYEE_RATE))
        pf_er = Decimal(_round(pf_wages * PF_EMPLOYER_RATE))
    else:
        pf_emp = pf_er = pf_wages = zero

    if Decimal(breakup.get("esic_employee") or 0) > 0:
        esic_emp = Decimal(_round(earned_gross * ESIC_EMPLOYEE_RATE))
        esic_er = Decimal(_round(earned_gross * ESIC_EMPLOYER_RATE))
    else:
        esic_emp = esic_er = zero

    pt = _pt_slab(getattr(emp, "pt_state", None), getattr(emp, "gender", None), earned_gross)
    return pf_emp, pf_er, esic_emp, esic_er, Decimal(pt), pf_wages


async def _resignation_settled(db: AsyncSession, employee_id: int) -> bool:
    from app.models import Resignation

    row = (
        await db.execute(
            select(Resignation.id)
            .where(Resignation.employee_id == employee_id)
            .where(Resignation.status == "settled")
            .limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def set_final_payslips_hold(
    db: AsyncSession, employee_id: int, *, on_hold: bool
) -> int:
    """Hold / release the final-settlement payslips of one employee.
    Called when a resignation is settled (release) or un-settled."""
    rows = (
        await db.execute(
            select(Payslip)
            .where(Payslip.employee_id == employee_id)
            .where(Payslip.is_final_settlement.is_(True))
        )
    ).scalars().all()
    for r in rows:
        r.on_hold = on_hold
    return len(rows)


# ── Run lifecycle ────────────────────────────────────────────────────
async def get_run(db: AsyncSession, run_id: int) -> PayrollRun:
    run = (
        await db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
    ).scalar_one_or_none()
    if not run:
        raise NotFoundError("Payroll run not found")
    return run


async def list_runs(db: AsyncSession) -> Sequence[PayrollRun]:
    return (
        await db.execute(
            select(PayrollRun)
            .order_by(PayrollRun.year.desc(), PayrollRun.month.desc())
        )
    ).scalars().all()


async def process_payroll(
    db: AsyncSession,
    *,
    year: int,
    month: int,
    cycle_start_day: Optional[int] = None,
    run_by: Optional[User] = None,
) -> PayrollRun:
    """Compute payslips for every active, salary-bearing employee.

    `cycle_start_day` controls the attendance window: 1 (or None) =
    plain calendar month; N>1 = N-of-previous-month → (N-1)-of-this
    month. When None, each employee's own attendance_cycle_start_day
    is used so mixed cycles in one run still work.
    """
    existing = (
        await db.execute(
            select(PayrollRun)
            .where(PayrollRun.year == year)
            .where(PayrollRun.month == month)
        )
    ).scalar_one_or_none()
    if existing and existing.status == "finalized":
        raise ConflictError("Payroll already finalized for this period")
    if existing and existing.disbursed:
        raise ConflictError("Payroll already disbursed for this period")

    if existing:
        # Re-process: clear payslips and reuse run record.
        for p in list(existing.payslips):
            await db.delete(p)
        run = existing
        run.status = "draft"
        run.cycle_start_day = cycle_start_day or 1
    else:
        run = PayrollRun(
            year=year,
            month=month,
            status="draft",
            cycle_start_day=cycle_start_day or 1,
            run_by=run_by.id if run_by else None,
        )
        db.add(run)
        await db.flush()

    from calendar import monthrange
    from datetime import date as _date

    period_days_int = monthrange(year, month)[1]

    # Everyone on the roll, including resigned / terminated employees
    # still serving notice. The per-employee attendance window decides
    # below who is actually paid in this run.
    employees = (
        await db.execute(
            select(Employee).where(
                Employee.status.in_(("active", "resigned", "terminated"))
            )
        )
    ).scalars().all()

    calc = JaikalkiSalaryCalculator()
    _policy = await get_leave_policy(db)
    from app.services.payroll_policy import get_payroll_policy

    _pay_policy = await get_payroll_policy(db)
    # PF wage ceiling for this wage month (day-weighted across the
    # calendar month, independent of the attendance cycle window).
    from app.services.pf_ceiling_service import ceilings_for_wage_month

    _ceil = await ceilings_for_wage_month(db, year, month)
    _pf_cap, _eps_cap, _edli_cap = _ceil["pf"], _ceil["eps"], _ceil["edli"]
    _basis = _pay_policy.get("division_basis", "calendar_days")

    total_gross = Decimal("0")
    total_net = Decimal("0")
    total_employer = Decimal("0")
    count = 0

    for emp in employees:
        cat = emp.category
        if not cat or not cat.has_salary or not emp.salary_template:
            # Interns / no-salary categories — skipped here. Their travel
            # reimbursements are processed via the intern reimbursement
            # endpoint instead.
            continue

        breakup = calc.calculate(
            emp.salary_template,
            ctc_annual=emp.ctc_annual or None,
            employee=emp,
            pf_cap=_pf_cap,
        ).as_dict()

        # Per-day class breakdown: holidays + Sundays drop out of the
        # divisor; LOP = absent days only (every approved leave counts
        # as paid by default — see `leave.all_approved_paid` policy).
        # Cycle window honours the employee's attendance_cycle_start_day
        # (e.g. 21st → 20th) unless the run explicitly overrides it.
        eff_cycle = (
            cycle_start_day
            if cycle_start_day is not None
            else (emp.attendance_cycle_start_day or 1)
        )
        win_first, win_last = cycle_window(year, month, eff_cycle)
        # Skip anyone who left before this window started or joins
        # after it ends — they have nothing to be paid for here.
        if emp.exit_date and emp.exit_date < win_first:
            continue
        if emp.date_of_joining and emp.date_of_joining > win_last:
            continue

        att = await compute_attendance_month(
            db,
            emp.id,
            year=year,
            month=month,
            cycle_start_day=eff_cycle,
            treat_all_leave_as_paid=bool(_policy.get("all_approved_paid", True)),
            sandwich_absent=bool(_policy.get("sandwich_absent_enabled", True)),
            service_from=emp.date_of_joining,
            service_to=emp.exit_date,
        )
        lop = att.days_lop

        # ── Divisor + scaling ────────────────────────────────────────
        # Attendance comes from the cycle window (e.g. 21-Aug → 20-Sep
        # for September). Pay is expressed over the target month so the
        # slip reads "Days Paid X / 30" for September:
        #     paid_days = period_days × (days_on_roll − LOP) ÷ window_days
        # Days before joining / after exit are excluded from
        # days_on_roll, so join/exit pro-rating stays inside the same
        # window as the attendance it is compared against.
        if _basis == "working_days":
            divisor = att.working_days
            paid_days_num = max(Decimal("0"), att.days_paid)
        else:
            divisor = (
                Decimal(30) if _basis == "fixed_30" else Decimal(period_days_int)
            )
            earned_days = max(Decimal("0"), att.days_on_roll - lop)
            paid_days_num = (
                divisor * earned_days / Decimal(att.window_days)
                if att.window_days
                else Decimal("0")
            ).quantize(Decimal("0.01"))

        scaling = (
            min(Decimal("1"), paid_days_num / divisor) if divisor > 0 else Decimal("0")
        )
        working = divisor
        paid = paid_days_num

        gross = (Decimal(breakup["gross"]) * scaling).quantize(Decimal("1"))
        pf_emp, pf_er, esic_emp, esic_er, pt, pf_wages = _earned_statutory(
            breakup, scaling, gross, emp, _pf_cap
        )
        eps_wages = (
            min(pf_wages, _eps_cap).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            if getattr(emp, "eps_member", True)
            else Decimal("0")
        )
        edli_wages = min(pf_wages, _edli_cap).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        # TDS: placeholder zero. Real slab calc deferred (see TODO).
        tds = Decimal("0")

        # Reimbursements approved before the run date and not yet paid
        # are added to the net pay and marked paid.
        rb_rows = (
            await db.execute(
                select(Reimbursement)
                .where(Reimbursement.employee_id == emp.id)
                .where(Reimbursement.status == "approved")
            )
        ).scalars().all()
        rb_total = sum((r.amount for r in rb_rows), Decimal("0"))

        deductions = pf_emp + esic_emp + pt + tds
        # Never pay out a negative amount.
        net = max(Decimal("0"), gross - deductions + rb_total)

        employer_cost = gross + pf_er + esic_er

        # Final salary: resigned / terminated employee whose last
        # working day falls inside this window. Held until the
        # resignation is marked settled.
        is_final = bool(
            emp.status in ("resigned", "terminated")
            and emp.exit_date is not None
            and emp.exit_date <= win_last
        )
        on_hold = is_final and not await _resignation_settled(db, emp.id)

        ps = Payslip(
            payroll_run_id=run.id,
            employee_id=emp.id,
            year=year,
            month=month,
            breakup=breakup,
            basic=Decimal(breakup["basic"]),
            hra=Decimal(breakup["hra"]),
            other_allowance=Decimal(breakup["other_allowance"]),
            gross=gross,
            pf_employee=pf_emp,
            esic_employee=esic_emp,
            professional_tax=pt,
            tds=tds,
            other_deductions=Decimal("0"),
            total_deductions=deductions,
            net_pay=net,
            pf_employer=pf_er,
            esic_employer=esic_er,
            days_paid=paid,
            days_lop=lop,
            working_days=working,
            days_present=att.days_present,
            days_paid_leave=att.days_paid_leave,
            days_unpaid_leave=att.days_unpaid_leave,
            days_absent=att.days_absent,
            days_holiday=att.days_holiday,
            days_weekoff=att.days_weekoff,
            days_sandwich=att.days_sandwich,
            is_final_settlement=is_final,
            on_hold=on_hold,
            pf_wages=pf_wages,
            eps_wages=eps_wages,
            edli_wages=edli_wages,
        )
        db.add(ps)
        await db.flush()

        # Attach reimbursements to this run.
        for r in rb_rows:
            r.status = "paid"
            r.paid_in_run_id = run.id

        total_gross += gross
        total_net += net
        total_employer += employer_cost
        count += 1

    run.total_gross = total_gross
    run.total_net = total_net
    run.total_employer_cost = total_employer
    run.total_employees = count
    run.status = "processed"
    run.run_at = _now()
    if run_by:
        run.run_by = run_by.id

    await db.commit()
    await db.refresh(run)
    return run


async def finalize_run(
    db: AsyncSession, run_id: int, *, finalized_by: Optional[User] = None
) -> PayrollRun:
    run = await get_run(db, run_id)
    if run.status == "finalized":
        raise ConflictError("Already finalized")
    if run.status != "processed":
        raise ValidationError("Only processed runs can be finalized")
    run.status = "finalized"
    run.finalized_at = _now()
    if finalized_by:
        run.finalized_by = finalized_by.id
    await db.commit()
    await db.refresh(run)
    return run


async def revert_run(db: AsyncSession, run_id: int) -> PayrollRun:
    run = await get_run(db, run_id)
    if run.status == "finalized":
        raise ConflictError("Cannot revert a finalized run")
    run.status = "reverted"
    # Roll back paid reimbursements
    rb = (
        await db.execute(
            select(Reimbursement).where(Reimbursement.paid_in_run_id == run_id)
        )
    ).scalars().all()
    for r in rb:
        r.status = "approved"
        r.paid_in_run_id = None
    for p in list(run.payslips):
        await db.delete(p)
    await db.commit()
    await db.refresh(run)
    return run


async def delete_run(db: AsyncSession, run_id: int) -> None:
    """Hard-delete a payroll run + its payslips. Blocked once the
    salary has been disbursed (the money already moved — keep the
    audit trail). Any reimbursements paid in the run are released."""
    run = await get_run(db, run_id)
    if run.disbursed:
        raise ConflictError(
            "Run is marked disbursed — cannot delete. Revert the "
            "disbursement first if this was a mistake."
        )
    rb = (
        await db.execute(
            select(Reimbursement).where(Reimbursement.paid_in_run_id == run_id)
        )
    ).scalars().all()
    for r in rb:
        r.status = "approved"
        r.paid_in_run_id = None
    await db.delete(run)  # payslips cascade
    await db.commit()


async def mark_disbursed(
    db: AsyncSession, run_id: int, *, by_user: Optional[User] = None
) -> PayrollRun:
    """Flag the run as salary-distributed/completed. Only a finalized
    run can be disbursed."""
    run = await get_run(db, run_id)
    if run.status != "finalized":
        raise ValidationError(
            "Finalize the run before marking salary distributed"
        )
    if run.disbursed:
        raise ConflictError("Run already marked disbursed")
    run.disbursed = True
    run.disbursed_at = _now()
    run.disbursed_by = by_user.id if by_user else None
    await db.commit()
    await db.refresh(run)
    return run


async def undo_disbursed(db: AsyncSession, run_id: int) -> PayrollRun:
    run = await get_run(db, run_id)
    run.disbursed = False
    run.disbursed_at = None
    run.disbursed_by = None
    await db.commit()
    await db.refresh(run)
    return run


def build_run_csv(
    run: PayrollRun,
    payslips: Sequence[Payslip],
    employees: dict[int, "Employee"],
) -> str:
    """Full payroll-run export — one row per employee with the salary
    breakup, statutory deductions, day counts and net pay."""
    import csv as _csv
    import io as _io

    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow([
        "employee_code", "name", "pf_number", "uan", "esic_number",
        "basic", "hra", "other_allowance", "gross",
        "pf_employee", "esic_employee", "professional_tax", "tds",
        "other_deductions", "total_deductions", "net_pay",
        "pf_employer", "esic_employer",
        "days_present", "days_paid_leave", "days_unpaid_leave",
        "days_absent", "days_paid", "days_lop", "working_days",
    ])
    for p in payslips:
        e = employees.get(p.employee_id)
        w.writerow([
            e.employee_code if e else p.employee_id,
            f"{e.first_name} {e.last_name}" if e else "",
            (e.pf_number if e else "") or "",
            (e.uan_number if e else "") or "",
            (e.esic_number if e else "") or "",
            p.basic, p.hra, p.other_allowance, p.gross,
            p.pf_employee, p.esic_employee, p.professional_tax, p.tds,
            p.other_deductions, p.total_deductions, p.net_pay,
            p.pf_employer, p.esic_employer,
            p.days_present, p.days_paid_leave, p.days_unpaid_leave,
            p.days_absent, p.days_paid, p.days_lop, p.working_days,
        ])
    return buf.getvalue()


# ── PF ECR (EPFO Electronic Challan-cum-Return) ───────────────────────
# One line per member, 11 fields joined by "#~#", no header row:
#   UAN, Name, Gross wages, EPF wages, EPS wages, EDLI wages,
#   EPF contribution (employee 12%), EPS contribution (8.33% of EPS wages),
#   EPF-EPS difference (employee share − EPS), NCP days, Refund of advances
_ECR_LEGACY_CAP = Decimal("15000")
_ECR_EE_RATE = Decimal("0.12")
_ECR_EPS_RATE = Decimal("0.0833")


def _r(v) -> int:
    """Round half up to whole rupees, as the EPFO portal does."""
    return int(Decimal(str(v or 0)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _ecr_name(e: "Employee") -> str:
    name = f"{e.first_name or ''} {e.last_name or ''}".upper()
    name = name.replace("#", " ").replace("~", " ")
    return " ".join(name.split())


def ecr_rows(
    payslips: Sequence[Payslip], employees: dict[int, "Employee"]
) -> tuple[list[dict], list[dict]]:
    """Build ECR rows. Returns (rows, excluded) where excluded lists
    employees with PF deducted but no UAN on record."""
    rows: list[dict] = []
    excluded: list[dict] = []
    for p in payslips:
        e = employees.get(p.employee_id)
        if e is None or Decimal(p.pf_employee or 0) <= 0:
            continue
        uan = (e.uan_number or "").strip()
        if not uan:
            excluded.append({
                "employee_id": e.id,
                "employee_code": e.employee_code,
                "name": _ecr_name(e),
                "reason": "No UAN on record",
            })
            continue

        stored = Decimal(getattr(p, "pf_wages", 0) or 0) > 0
        if stored:
            epf_wages = _r(p.pf_wages)
            eps_wages = _r(getattr(p, "eps_wages", 0))
            edli_raw = Decimal(getattr(p, "edli_wages", 0) or 0)
            edli_wages = _r(edli_raw) if edli_raw > 0 else min(epf_wages, int(_ECR_LEGACY_CAP))
        else:
            # Payslips from before PF wages were stored: earned basic
            # capped at the old ₹15,000 ceiling.
            working = Decimal(p.working_days or 0)
            ratio = (Decimal(p.days_paid or 0) / working) if working > 0 else Decimal(1)
            epf_wages = _r(min(Decimal(p.basic or 0) * min(ratio, Decimal(1)), _ECR_LEGACY_CAP))
            eps_wages = epf_wages if getattr(e, "eps_member", True) else 0
            edli_wages = epf_wages

        ee = _r(Decimal(epf_wages) * _ECR_EE_RATE)
        eps = _r(Decimal(eps_wages) * _ECR_EPS_RATE)
        rows.append({
            "employee_id": e.id,
            "employee_code": e.employee_code,
            "uan": uan,
            "name": _ecr_name(e),
            "gross_wages": _r(p.gross),
            "epf_wages": epf_wages,
            "eps_wages": eps_wages,
            "edli_wages": edli_wages,
            "epf_contri": ee,
            "eps_contri": eps,
            "epf_eps_diff": ee - eps,
            "ncp_days": _r(p.days_lop),
            "refund": 0,
            "payslip_pf_employee": _r(p.pf_employee),
        })
    return rows, excluded


_ECR_FIELDS = (
    "uan", "name", "gross_wages", "epf_wages", "eps_wages", "edli_wages",
    "epf_contri", "eps_contri", "epf_eps_diff", "ncp_days", "refund",
)


def ecr_text(rows: list[dict]) -> str:
    """Data rows only — the EPFO portal rejects header / comment lines."""
    lines = ["#~#".join(str(r[f]) for f in _ECR_FIELDS) for r in rows]
    return "\n".join(lines) + ("\n" if lines else "")


def validate_ecr_rows(
    rows: list[dict],
    *,
    pf_cap: Decimal,
    eps_cap: Decimal,
    edli_cap: Decimal,
    days_in_month: int,
) -> list[dict]:
    """Check every row against the portal's rules. Each issue is
    {employee_code, name, level: error|warning, message}."""
    issues: list[dict] = []

    def add(r, level, msg):
        issues.append({"employee_code": r["employee_code"], "name": r["name"],
                       "level": level, "message": msg})

    eps_limit = _r(eps_cap)
    edli_limit = _r(edli_cap)
    pf_limit = _r(pf_cap)
    for r in rows:
        if not (r["uan"].isdigit() and len(r["uan"]) == 12):
            add(r, "error", f"UAN '{r['uan']}' must be 12 digits")
        if r["epf_contri"] != _r(Decimal(r["epf_wages"]) * _ECR_EE_RATE):
            add(r, "error", "EPF contribution is not 12% of EPF wages")
        if r["eps_contri"] != _r(Decimal(r["eps_wages"]) * _ECR_EPS_RATE):
            add(r, "error", "EPS contribution is not 8.33% of EPS wages")
        if r["epf_eps_diff"] != r["epf_contri"] - r["eps_contri"] or r["epf_eps_diff"] < 0:
            add(r, "error", "EPF-EPS difference must equal EPF contribution − EPS contribution")
        if r["epf_wages"] > r["gross_wages"]:
            add(r, "error", "EPF wages exceed gross wages")
        if r["eps_wages"] > r["epf_wages"]:
            add(r, "error", "EPS wages exceed EPF wages")
        if r["edli_wages"] > r["epf_wages"]:
            add(r, "error", "EDLI wages exceed EPF wages")
        if r["eps_wages"] > eps_limit:
            add(r, "error", f"EPS wages exceed the EPS ceiling (₹{eps_limit:,})")
        if r["edli_wages"] > edli_limit:
            add(r, "error", f"EDLI wages exceed the EDLI ceiling (₹{edli_limit:,})")
        if not (0 <= r["ncp_days"] <= days_in_month):
            add(r, "error", f"NCP days must be between 0 and {days_in_month}")
        if r["epf_wages"] > pf_limit:
            add(r, "warning", f"EPF wages above the PF ceiling (₹{pf_limit:,}) — "
                              "fine only if this member contributes on higher wages")
        if r["payslip_pf_employee"] != r["epf_contri"]:
            add(r, "warning", f"Payslip deducted ₹{r['payslip_pf_employee']:,} PF but the "
                              f"challan shows ₹{r['epf_contri']:,}")
    return issues


def build_pf_ecr(
    run: PayrollRun,
    payslips: Sequence[Payslip],
    employees: dict[int, "Employee"],
) -> str:
    rows, _excluded = ecr_rows(payslips, employees)
    return ecr_text(rows)


# ── Reads ─────────────────────────────────────────────────────────────
async def list_payslips_for_employee(
    db: AsyncSession,
    employee_id: int,
    *,
    only_disbursed: bool = False,
) -> Sequence[Payslip]:
    """Return payslips for an employee.

    When ``only_disbursed`` is True (the default for the employee's own
    self-service endpoint), drafts and finalized-but-not-yet-paid runs
    are filtered out — the employee should only see a slip once the
    salary has actually been credited. Admin paths leave this off so
    they can review in-flight runs.
    """
    stmt = (
        select(Payslip)
        .where(Payslip.employee_id == employee_id)
        .order_by(Payslip.year.desc(), Payslip.month.desc())
    )
    if only_disbursed:
        # Require BOTH conditions so a "processed" or "draft" run can
        # never leak into the employee's mobile slip list, even if some
        # legacy row had `disbursed` flipped without going through the
        # finalize step.
        stmt = stmt.join(
            PayrollRun, Payslip.payroll_run_id == PayrollRun.id
        ).where(
            PayrollRun.status == "finalized",
            PayrollRun.disbursed.is_(True),
            Payslip.on_hold.is_(False),
        )
    return (await db.execute(stmt)).scalars().all()


async def is_run_disbursed(db: AsyncSession, payslip: Payslip) -> bool:
    """True iff the parent run is BOTH finalized AND marked disbursed —
    matches the visibility rule used by list_payslips_for_employee.
    Used to gate the self-PDF download."""
    run = (
        await db.execute(
            select(PayrollRun).where(PayrollRun.id == payslip.payroll_run_id)
        )
    ).scalar_one_or_none()
    return bool(
        run
        and run.status == "finalized"
        and run.disbursed
        and not getattr(payslip, "on_hold", False)
    )


async def get_payslip(db: AsyncSession, payslip_id: int) -> Payslip:
    p = (
        await db.execute(select(Payslip).where(Payslip.id == payslip_id))
    ).scalar_one_or_none()
    if not p:
        raise NotFoundError("Payslip not found")
    return p


# ── Bank file export (generic CSV) ────────────────────────────────────
def build_bank_csv(payslips: Sequence[Payslip], employees: dict[int, Employee]) -> str:
    """Generate a generic CSV bank file. Returns the CSV text."""
    lines = ["employee_code,full_name,bank_account,ifsc,amount"]
    for p in payslips:
        # Final salaries on hold are not transferred until the
        # resignation is settled.
        if getattr(p, "on_hold", False):
            continue
        emp = employees.get(p.employee_id)
        if not emp:
            continue
        bank = None
        # Bank details may not be present; placeholder if missing.
        for rel in getattr(emp, "_sa_instance_state", None) and [] or []:
            pass
        lines.append(
            f"{emp.employee_code},{emp.first_name} {emp.last_name},,,{p.net_pay}"
        )
    return "\n".join(lines) + "\n"

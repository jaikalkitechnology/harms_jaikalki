"""Payroll engine: bulk-process monthly payroll, generate payslips."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
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
from app.services.payroll_attendance import compute_attendance_month
from app.services.salary_calculator import JaikalkiSalaryCalculator


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


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

    employees = (
        await db.execute(
            select(Employee).where(Employee.status == "active")
        )
    ).scalars().all()

    calc = JaikalkiSalaryCalculator()
    _policy = await get_leave_policy(db)

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
        att = await compute_attendance_month(
            db,
            emp.id,
            year=year,
            month=month,
            cycle_start_day=eff_cycle,
            treat_all_leave_as_paid=bool(_policy.get("all_approved_paid", True)),
        )
        working = att.working_days
        lop = att.days_lop
        paid = att.days_paid
        scaling = paid / working if working > 0 else Decimal("0")

        gross = (Decimal(breakup["gross"]) * scaling).quantize(Decimal("1"))
        pf_emp = Decimal(breakup["pf_employee"])  # capped → don't scale
        esic_emp = Decimal(breakup["esic_employee"])
        pt = Decimal(breakup["professional_tax"])
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
        net = gross - deductions + rb_total

        pf_er = Decimal(breakup["pf_employer"])
        esic_er = Decimal(breakup["esic_employer"])
        employer_cost = gross + pf_er + esic_er

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


def build_pf_ecr(
    run: PayrollRun,
    payslips: Sequence[Payslip],
    employees: dict[int, "Employee"],
) -> str:
    """EPFO ECR (Electronic Challan-cum-Return) text file, '#~#'
    delimited, one line per member with a UAN. PF wages are capped at
    ₹15,000; EPS = 8.33% of capped wages, EPF = employee 12% and the
    employer balance. Only employees with a UAN and non-zero PF are
    included — file this on the EPFO Unified Portal."""
    PF_CAP = Decimal("15000")
    lines: list[str] = []
    for p in payslips:
        e = employees.get(p.employee_id)
        if not e or not (e.uan_number or "").strip():
            continue
        pf_emp = Decimal(p.pf_employee or 0)
        if pf_emp <= 0:
            continue
        # Derive PF wages from the capped basic the calculator used.
        pf_wages = min(Decimal(p.basic or 0), PF_CAP)
        pf_wages = pf_wages.quantize(Decimal("1"))
        eps_wages = pf_wages
        edli_wages = pf_wages
        eps_contri = (eps_wages * Decimal("0.0833")).quantize(Decimal("1"))
        epf_contri = pf_emp.quantize(Decimal("1"))
        # Employer EPF share = employer total − EPS.
        er_total = Decimal(p.pf_employer or 0).quantize(Decimal("1"))
        er_epf = max(Decimal("0"), er_total - eps_contri)
        diff = (epf_contri + er_epf) - epf_contri  # employer EPF portion
        ncp_days = int(Decimal(p.days_lop or 0))
        name = f"{e.first_name} {e.last_name}".strip().upper()
        lines.append(
            "#~#".join(
                str(x)
                for x in [
                    (e.uan_number or "").strip(),
                    name,
                    int(pf_wages),       # Gross wages
                    int(pf_wages),       # EPF wages
                    int(eps_wages),      # EPS wages
                    int(edli_wages),     # EDLI wages
                    int(epf_contri),     # EPF contri remitted (employee)
                    int(eps_contri),     # EPS contri remitted
                    int(diff),           # EPF EPS diff remitted (employer EPF)
                    ncp_days,            # NCP days
                    0,                   # Refund of advances
                ]
            )
        )
    header = (
        f"# Jaikalki PF ECR — {run.year}-{run.month:02d} "
        f"(cycle start {run.cycle_start_day})\n"
        f"# UAN#~#Name#~#GrossWages#~#EPFWages#~#EPSWages#~#EDLIWages"
        f"#~#EPFContri#~#EPSContri#~#EPFEPSDiff#~#NCPDays#~#Refund\n"
    )
    return header + "\n".join(lines) + ("\n" if lines else "")


# ── Reads ─────────────────────────────────────────────────────────────
async def list_payslips_for_employee(
    db: AsyncSession, employee_id: int
) -> Sequence[Payslip]:
    return (
        await db.execute(
            select(Payslip)
            .where(Payslip.employee_id == employee_id)
            .order_by(Payslip.year.desc(), Payslip.month.desc())
        )
    ).scalars().all()


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

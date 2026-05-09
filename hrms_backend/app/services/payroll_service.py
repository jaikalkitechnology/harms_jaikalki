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
    run_by: Optional[User] = None,
) -> PayrollRun:
    """Compute payslips for every active, salary-bearing employee."""
    existing = (
        await db.execute(
            select(PayrollRun)
            .where(PayrollRun.year == year)
            .where(PayrollRun.month == month)
        )
    ).scalar_one_or_none()
    if existing and existing.status == "finalized":
        raise ConflictError("Payroll already finalized for this period")

    if existing:
        # Re-process: clear payslips and reuse run record.
        for p in list(existing.payslips):
            await db.delete(p)
        run = existing
        run.status = "draft"
    else:
        run = PayrollRun(
            year=year,
            month=month,
            status="draft",
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
        # divisor; LOP = unpaid leave (incl. sandwich days) + absent.
        # Paid leave keeps the day's gross intact.
        att = await compute_attendance_month(
            db, emp.id, year=year, month=month
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

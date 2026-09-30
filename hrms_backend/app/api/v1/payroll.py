from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import (
    Employee,
    GeneratedDocument,
    InternTravelExpense,
    PayrollRun,
    Payslip,
    Reimbursement,
    User,
)
from app.schemas.payroll import (
    BankFileExportOut,
    GeneratedDocumentOut,
    InvestmentDeclarationCreate,
    InvestmentDeclarationOut,
    PayrollRunDetail,
    PayrollRunOut,
    PayrollRunRequest,
    PayslipOut,
    ReimbursementCreate,
    ReimbursementDecision,
    ReimbursementOut,
)
from app.services import employee_service as emp_svc
from app.services import jaikalki_documents as docs
from app.services import payroll_service

router = APIRouter(prefix="/payroll", tags=["payroll"])


# ── Payroll runs ──────────────────────────────────────────────────────
@router.get("/runs", response_model=list[PayrollRunOut])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    return await payroll_service.list_runs(db)


@router.post(
    "/run",
    response_model=PayrollRunOut,
    status_code=status.HTTP_201_CREATED,
)
async def run_payroll(
    payload: PayrollRunRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await payroll_service.process_payroll(
        db,
        year=payload.year,
        month=payload.month,
        cycle_start_day=payload.cycle_start_day,
        run_by=user,
    )


@router.post("/runs/{run_id}/finalize", response_model=PayrollRunOut)
async def finalize_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await payroll_service.finalize_run(
        db, run_id, finalized_by=user
    )


@router.post("/runs/{run_id}/revert", response_model=PayrollRunOut)
async def revert_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    return await payroll_service.revert_run(db, run_id)


@router.delete(
    "/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    await payroll_service.delete_run(db, run_id)


@router.post("/runs/{run_id}/disburse", response_model=PayrollRunOut)
async def disburse_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await payroll_service.mark_disbursed(db, run_id, by_user=user)


@router.post("/runs/{run_id}/undo-disburse", response_model=PayrollRunOut)
async def undo_disburse_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    return await payroll_service.undo_disbursed(db, run_id)


@router.get("/runs/{run_id}/export.csv")
async def export_run_csv(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    run = await payroll_service.get_run(db, run_id)
    emps = (await db.execute(select(Employee))).scalars().all()
    by_id = {e.id: e for e in emps}
    csv_text = payroll_service.build_run_csv(run, run.payslips, by_id)
    fname = f"payroll-{run.year}-{run.month:02d}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/runs/{run_id}/pf-challan.txt")
async def export_pf_challan(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    run = await payroll_service.get_run(db, run_id)
    emps = (await db.execute(select(Employee))).scalars().all()
    by_id = {e.id: e for e in emps}
    ecr = payroll_service.build_pf_ecr(run, run.payslips, by_id)
    fname = f"pf-ecr-{run.year}-{run.month:02d}.txt"
    return Response(
        content=ecr,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/runs/{run_id}/pf-challan/check")
async def check_pf_challan(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    """Validate the ECR against the EPFO portal's rules before download."""
    from calendar import monthrange

    from app.services.pf_ceiling_service import ceilings_for_wage_month

    run = await payroll_service.get_run(db, run_id)
    emps = (await db.execute(select(Employee))).scalars().all()
    by_id = {e.id: e for e in emps}
    rows, excluded = payroll_service.ecr_rows(run.payslips, by_id)
    ceil = await ceilings_for_wage_month(db, run.year, run.month)
    issues = payroll_service.validate_ecr_rows(
        rows,
        pf_cap=ceil["pf"],
        eps_cap=ceil["eps"],
        edli_cap=ceil["edli"],
        days_in_month=monthrange(run.year, run.month)[1],
    )
    errors = sum(1 for i in issues if i["level"] == "error")
    return {
        "run_id": run.id,
        "wage_month": f"{run.year}-{run.month:02d}",
        "ceilings": {k: str(v) for k, v in ceil.items()},
        "rows": rows,
        "excluded": excluded,
        "issues": issues,
        "errors": errors,
        "warnings": len(issues) - errors,
        "ok": errors == 0,
        "totals": {
            "members": len(rows),
            "epf_wages": sum(r["epf_wages"] for r in rows),
            "epf_contri": sum(r["epf_contri"] for r in rows),
            "eps_contri": sum(r["eps_contri"] for r in rows),
            "epf_eps_diff": sum(r["epf_eps_diff"] for r in rows),
        },
    }


@router.get("/runs/{run_id}", response_model=PayrollRunDetail)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    run = await payroll_service.get_run(db, run_id)
    return PayrollRunDetail(
        run=PayrollRunOut.model_validate(run),
        payslips=[PayslipOut.model_validate(p) for p in run.payslips],
    )


# ── Payslips ──────────────────────────────────────────────────────────
@router.get("/payslips/me", response_model=list[PayslipOut])
async def my_payslips(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record")
    # Self-service: only surface a slip once the run is finalized AND
    # marked disbursed (salary paid). Draft / processed / finalized but
    # not-yet-paid runs are visible only to HR / admin on the runs page.
    rows = await payroll_service.list_payslips_for_employee(
        db, emp.id, only_disbursed=True
    )
    # Force every hop to fetch fresh — without this a CDN / proxy can
    # serve a stale list from before the disbursed gate was deployed.
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Payslip-Filter"] = "finalized+disbursed"
    import logging
    logging.getLogger(__name__).info(
        "my_payslips emp=%s returning=%d (only_disbursed=True)",
        emp.id, len(rows),
    )
    return rows


@router.get("/payslips/{payslip_id}/pdf")
async def download_payslip(
    payslip_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    payslip = await payroll_service.get_payslip(db, payslip_id)
    target = await emp_svc.get_employee(db, payslip.employee_id)
    allowed = await emp_svc.visible_employee_ids(db, user)
    emp_svc.assert_can_view(user, target, allowed)
    # The employee may only pull their own slip once salary is paid.
    # Admin / manager (visible_employee_ids returns None or includes
    # the target) keep early access for audit / corrections.
    if target.user_id == user.id and not emp_svc.can_see_all(user):
        if not await payroll_service.is_run_disbursed(db, payslip):
            raise ForbiddenError(
                "This payslip is not yet finalized. It will be "
                "available once the salary has been paid."
            )
    from app.models import EmployeeBankDetails as _Bank
    from sqlalchemy import select as _select
    bank = (
        await db.execute(
            _select(_Bank).where(_Bank.employee_id == target.id)
        )
    ).scalar_one_or_none()
    pdf = docs.render_payslip_pdf(payslip, target, bank=bank)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="payslip_{target.employee_code}_'
                f'{payslip.year}_{payslip.month:02d}.pdf"'
            )
        },
    )


# ── Offer letter / confirmation letter ────────────────────────────────
@router.post(
    "/offer-letter/{employee_id}",
    response_model=GeneratedDocumentOut,
)
async def generate_offer_letter(
    employee_id: int,
    on_date: Optional[date] = Query(
        default=None, description="Letter date (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.create")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    _, doc = await docs.generate_offer_letter(
        db, emp, generated_by=user, on_date=on_date
    )
    return doc


@router.get("/offer-letter/{employee_id}/preview")
async def preview_offer_letter(
    employee_id: int,
    on_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.create")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    pdf, _doc = await docs.generate_offer_letter(
        db, emp, generated_by=user, upload_to_storage=False, on_date=on_date
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="offer_letter_{emp.employee_code}.pdf"'
            )
        },
    )


@router.post(
    "/confirmation-letter/{employee_id}",
    response_model=GeneratedDocumentOut,
)
async def generate_confirmation_letter(
    employee_id: int,
    on_date: Optional[date] = Query(
        default=None, description="Letter date (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    _, doc = await docs.generate_confirmation_letter(
        db, emp, generated_by=user, on_date=on_date
    )
    return doc


@router.delete(
    "/confirmation-letter/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_confirmation_letter(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    """Delete the most-recent confirmation letter and revert the
    employee: clears confirmation_date, puts them back on probation,
    and restores the originally-planned probation end date."""
    emp = await emp_svc.get_employee(db, employee_id)
    doc = (
        await db.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.employee_id == employee_id)
            .where(GeneratedDocument.doc_type == "confirmation_letter")
            .order_by(GeneratedDocument.created_at.desc())
        )
    ).scalars().first()
    if doc is None:
        raise NotFoundError("No confirmation letter to delete")
    await db.delete(doc)
    await db.commit()
    await emp_svc.revert_confirmation(db, emp)


@router.get(
    "/documents/{employee_id}",
    response_model=list[GeneratedDocumentOut],
)
async def list_employee_documents(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = await emp_svc.get_employee(db, employee_id)
    allowed = await emp_svc.visible_employee_ids(db, user)
    emp_svc.assert_can_view(user, target, allowed)
    rows = (
        await db.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.employee_id == employee_id)
            .order_by(GeneratedDocument.created_at.desc())
        )
    ).scalars().all()
    return rows


# ── Reimbursements ────────────────────────────────────────────────────
@router.post(
    "/reimbursements",
    response_model=ReimbursementOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_reimbursement(
    payload: ReimbursementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record")
    obj = Reimbursement(
        employee_id=emp.id,
        category=payload.category,
        amount=payload.amount,
        bill_date=payload.bill_date,
        bill_url=payload.bill_url,
        description=payload.description,
        status="pending",
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/reimbursements/me", response_model=list[ReimbursementOut])
async def my_reimbursements(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        return []
    return (
        await db.execute(
            select(Reimbursement)
            .where(Reimbursement.employee_id == emp.id)
            .order_by(Reimbursement.created_at.desc())
        )
    ).scalars().all()


@router.get(
    "/reimbursements/pending",
    response_model=list[ReimbursementOut],
)
async def pending_reimbursements(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    visible = await emp_svc.visible_employee_ids(db, user)
    stmt = select(Reimbursement).where(Reimbursement.status == "pending")
    if visible is not None:
        if not visible:
            return []
        stmt = stmt.where(Reimbursement.employee_id.in_(visible))
    stmt = stmt.order_by(Reimbursement.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


@router.get("/reimbursements", response_model=list[ReimbursementOut])
async def list_reimbursements(
    rb_status: Optional[str] = Query(default=None, alias="status"),
    employee_id: Optional[int] = None,
    category: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    """Admin list of reimbursements across every status (pending /
    approved / rejected / paid). Approved-but-not-paid claims are added
    to net pay in the next payroll run; once paid, status flips to
    `paid` and the row links to that run via paid_in_run_id."""
    from sqlalchemy import or_

    visible = await emp_svc.visible_employee_ids(db, user)
    stmt = select(Reimbursement)
    if visible is not None:
        if not visible:
            return []
        stmt = stmt.where(Reimbursement.employee_id.in_(visible))
    if rb_status:
        stmt = stmt.where(Reimbursement.status == rb_status)
    if employee_id is not None:
        stmt = stmt.where(Reimbursement.employee_id == employee_id)
    if category:
        stmt = stmt.where(Reimbursement.category == category)
    if from_date is not None:
        stmt = stmt.where(Reimbursement.bill_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(Reimbursement.bill_date <= to_date)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Reimbursement.description.ilike(like),
                Reimbursement.category.ilike(like),
                Reimbursement.rejection_reason.ilike(like),
            )
        )
    stmt = stmt.order_by(Reimbursement.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/reimbursements/{reimbursement_id}/approve",
    response_model=ReimbursementOut,
)
async def approve_reimbursement(
    reimbursement_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    obj = (
        await db.execute(
            select(Reimbursement).where(Reimbursement.id == reimbursement_id)
        )
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Reimbursement not found")
    if obj.status != "pending":
        raise ValidationError("Already decided")
    obj.status = "approved"
    obj.approver_id = user.id
    obj.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.post(
    "/reimbursements/{reimbursement_id}/reject",
    response_model=ReimbursementOut,
)
async def reject_reimbursement(
    reimbursement_id: int,
    payload: ReimbursementDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    obj = (
        await db.execute(
            select(Reimbursement).where(Reimbursement.id == reimbursement_id)
        )
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Reimbursement not found")
    if obj.status != "pending":
        raise ValidationError("Already decided")
    obj.status = "rejected"
    obj.approver_id = user.id
    obj.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    obj.rejection_reason = payload.rejection_reason
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Investment declaration ────────────────────────────────────────────
@router.post(
    "/declaration",
    response_model=InvestmentDeclarationOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_declaration(
    payload: InvestmentDeclarationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models import InvestmentDeclaration

    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record")

    existing = (
        await db.execute(
            select(InvestmentDeclaration)
            .where(InvestmentDeclaration.employee_id == emp.id)
            .where(InvestmentDeclaration.fy == payload.fy)
        )
    ).scalar_one_or_none()
    if existing:
        if existing.locked_at:
            raise ValidationError("Declaration already locked")
        existing.regime = payload.regime
        existing.section_80c = payload.section_80c
        existing.section_80d = payload.section_80d
        existing.hra_exemption = payload.hra_exemption
        existing.home_loan_interest = payload.home_loan_interest
        existing.educational_loan = payload.educational_loan
        existing.donations_80g = payload.donations_80g
        existing.other = payload.other
        await db.commit()
        await db.refresh(existing)
        return existing

    obj = InvestmentDeclaration(
        employee_id=emp.id,
        **payload.model_dump(),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/declaration/me", response_model=Optional[InvestmentDeclarationOut])
async def my_declaration(
    fy: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models import InvestmentDeclaration

    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        return None
    stmt = (
        select(InvestmentDeclaration)
        .where(InvestmentDeclaration.employee_id == emp.id)
        .order_by(InvestmentDeclaration.fy.desc())
    )
    if fy:
        stmt = stmt.where(InvestmentDeclaration.fy == fy)
    return (await db.execute(stmt)).scalars().first()


# ── Bank file export (generic CSV) ────────────────────────────────────
@router.post(
    "/bank-file/{run_id}",
    response_model=BankFileExportOut,
)
async def export_bank_file(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.export")),
):
    from app.services.storage import upload_fileobj
    import io as _io

    from app.models import BankFileExport

    run = await payroll_service.get_run(db, run_id)
    employees = (
        await db.execute(
            select(Employee).where(
                Employee.id.in_({p.employee_id for p in run.payslips})
            )
        )
    ).scalars().all()
    by_id = {e.id: e for e in employees}
    csv_text = payroll_service.build_bank_csv(run.payslips, by_id)
    file_url = ""
    try:
        _, file_url = upload_fileobj(
            _io.BytesIO(csv_text.encode("utf-8")),
            key_prefix=f"bank-files/{run.year}-{run.month:02d}",
            filename=f"jaikalki-{run.year}-{run.month:02d}.csv",
            content_type="text/csv",
        )
    except Exception:
        file_url = f"local://bank-files/{run.year}-{run.month:02d}.csv"
    obj = BankFileExport(
        payroll_run_id=run.id,
        file_url=file_url,
        bank_format="csv",
        total_amount=run.total_net,
        total_employees=run.total_employees,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Intern travel expense reimbursement ───────────────────────────────
@router.post(
    "/intern-reimbursement/process",
    response_model=dict,
)
async def process_intern_reimbursement(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    """Mark all approved intern travel expenses for the month as reimbursed."""
    from calendar import monthrange

    from app.models import InternTravelExpense

    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])

    rows = (
        await db.execute(
            select(InternTravelExpense)
            .where(InternTravelExpense.expense_date >= first)
            .where(InternTravelExpense.expense_date <= last)
            .where(InternTravelExpense.status == "approved")
        )
    ).scalars().all()
    total = Decimal("0")
    by_intern: dict[int, Decimal] = {}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for r in rows:
        r.status = "reimbursed"
        r.reimbursed_at = now
        total += Decimal(r.amount or 0)
        by_intern[r.employee_id] = by_intern.get(r.employee_id, Decimal("0")) + (
            Decimal(r.amount or 0)
        )
    await db.commit()
    return {
        "year": year,
        "month": month,
        "total": str(total),
        "expenses": len(rows),
        "interns": len(by_intern),
        "by_intern": {str(k): str(v) for k, v in by_intern.items()},
    }


# ── PF wage ceiling register ──────────────────────────────────────────
from app.schemas.payroll import (  # noqa: E402
    PayrollPolicyOut,
    PayrollPolicyUpdate,
    PfCapCurrentOut,
    PfCeilingAbsorbRequest,
    PfCeilingCreate,
    PfCeilingImpactOut,
    PfCeilingOut,
    PfCeilingUpdate,
)
from app.services import pf_ceiling_service as pf_svc  # noqa: E402


async def _ceiling_out(db: AsyncSession, rec, today: date) -> PfCeilingOut:
    out = PfCeilingOut.model_validate(rec)
    out.applies_from = pf_svc.applies_from(rec)
    out.locked = await pf_svc._locked_by_payroll(db, out.applies_from)
    return out


@router.get("/pf-ceilings", response_model=list[PfCeilingOut], tags=["payroll"])
async def list_pf_ceilings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = date.today()
    records = await pf_svc.list_ceilings(db)
    outs = [await _ceiling_out(db, r, today) for r in records]
    # Status: the record currently in force is "active"; earlier ones
    # "past"; later ones "scheduled".
    active_idx = None
    for i, o in enumerate(outs):
        if o.applies_from and o.applies_from <= today:
            active_idx = i
    for i, o in enumerate(outs):
        if active_idx is not None and i == active_idx:
            o.status = "active"
        elif o.applies_from and o.applies_from > today:
            o.status = "scheduled"
        else:
            o.status = "past"
    return outs


@router.get("/pf-ceilings/current", response_model=PfCapCurrentOut, tags=["payroll"])
async def current_pf_cap(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = date.today()
    pf_cap, eps_cap = await pf_svc.cap_on(db, today)
    upcoming = [
        r for r in await pf_svc.list_ceilings(db) if pf_svc.applies_from(r) > today
    ]
    nxt = None
    if upcoming:
        upcoming.sort(key=pf_svc.applies_from)
        nxt = await _ceiling_out(db, upcoming[0], today)
        nxt.status = "scheduled"
    return PfCapCurrentOut(pf_cap=pf_cap, eps_cap=eps_cap, as_of=today, next_change=nxt)


@router.post(
    "/pf-ceilings",
    response_model=PfCeilingOut,
    status_code=status.HTTP_201_CREATED,
    tags=["payroll"],
)
async def create_pf_ceiling(
    payload: PfCeilingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    rec = await pf_svc.create(db, payload.model_dump(), actor=user)
    return await _ceiling_out(db, rec, date.today())


@router.put("/pf-ceilings/{ceiling_id}", response_model=PfCeilingOut, tags=["payroll"])
async def update_pf_ceiling(
    ceiling_id: int,
    payload: PfCeilingUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    rec = await pf_svc.update(db, ceiling_id, payload.model_dump(exclude_unset=True))
    return await _ceiling_out(db, rec, date.today())


@router.delete(
    "/pf-ceilings/{ceiling_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["payroll"],
)
async def delete_pf_ceiling(
    ceiling_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    await pf_svc.delete(db, ceiling_id)


@router.get(
    "/pf-ceilings/{ceiling_id}/impact",
    response_model=PfCeilingImpactOut,
    tags=["payroll"],
)
async def pf_ceiling_impact(
    ceiling_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    return await pf_svc.impact(db, ceiling_id)


@router.post("/pf-ceilings/{ceiling_id}/absorb", tags=["payroll"])
async def pf_ceiling_absorb(
    ceiling_id: int,
    payload: PfCeilingAbsorbRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await pf_svc.absorb(
        db,
        ceiling_id,
        employee_ids=payload.employee_ids,
        effective_date=payload.effective_date,
        reason=payload.reason,
        actor=user,
    )


# ── Payroll policy (payslip divisor) ──────────────────────────────────
@router.get("/policy", response_model=PayrollPolicyOut, tags=["payroll"])
async def get_payroll_policy_endpoint(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.services.payroll_policy import get_payroll_policy

    pol = await get_payroll_policy(db)
    return PayrollPolicyOut(division_basis=pol.get("division_basis", "calendar_days"))


@router.put("/policy", response_model=PayrollPolicyOut, tags=["payroll"])
async def set_payroll_policy_endpoint(
    payload: PayrollPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    from app.services.payroll_policy import set_payroll_policy

    pol = await set_payroll_policy(db, payload.model_dump(), actor=user)
    return PayrollPolicyOut(division_basis=pol.get("division_basis", "calendar_days"))

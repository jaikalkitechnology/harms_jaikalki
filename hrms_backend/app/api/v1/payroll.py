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
        db, year=payload.year, month=payload.month, run_by=user
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record")
    return await payroll_service.list_payslips_for_employee(db, emp.id)


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
    pdf = docs.render_payslip_pdf(payslip, target)
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.create")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    _, doc = await docs.generate_offer_letter(db, emp, generated_by=user)
    return doc


@router.get("/offer-letter/{employee_id}/preview")
async def preview_offer_letter(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.create")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    pdf, _doc = await docs.generate_offer_letter(
        db, emp, generated_by=user, upload_to_storage=False
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    _, doc = await docs.generate_confirmation_letter(db, emp, generated_by=user)
    return doc


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

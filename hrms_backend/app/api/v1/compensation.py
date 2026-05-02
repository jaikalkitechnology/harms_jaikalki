from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.compensation import (
    SalaryRevisionOut,
    SalaryRevisionPropose,
    SalaryRevisionRejectBody,
)
from app.services import compensation_service as svc

router = APIRouter(prefix="/compensation", tags=["compensation"])


@router.post(
    "/revisions",
    response_model=SalaryRevisionOut,
    status_code=status.HTTP_201_CREATED,
)
async def propose_revision(
    payload: SalaryRevisionPropose,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
) -> SalaryRevisionOut:
    return await svc.propose(
        db,
        proposer=user,
        employee_id=payload.employee_id,
        new_ctc_annual=payload.new_ctc_annual,
        effective_date=payload.effective_date,
        reason=payload.reason,
        new_template_id=payload.new_salary_template_id,
        new_designation_id=payload.new_designation_id,
        notes=payload.notes,
    )


@router.get(
    "/revisions/pending",
    response_model=list[SalaryRevisionOut],
)
async def list_pending(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("payroll.run")),
):
    return await svc.list_pending_approval(db)


@router.get(
    "/revisions/employee/{employee_id}",
    response_model=list[SalaryRevisionOut],
)
async def list_for_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("salary.view.team")),
):
    return await svc.list_for_employee(db, employee_id)


@router.post("/revisions/{revision_id}/approve", response_model=SalaryRevisionOut)
async def approve(
    revision_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await svc.approve(db, revision_id, approver=user)


@router.post("/revisions/{revision_id}/reject", response_model=SalaryRevisionOut)
async def reject(
    revision_id: int,
    body: SalaryRevisionRejectBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await svc.reject(
        db, revision_id, approver=user, reason_text=body.reason
    )


@router.post("/revisions/{revision_id}/cancel", response_model=SalaryRevisionOut)
async def cancel(
    revision_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await svc.cancel(db, revision_id, actor=user)


@router.post("/revisions/{revision_id}/apply", response_model=SalaryRevisionOut)
async def apply(
    revision_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await svc.apply(db, revision_id, actor=user)

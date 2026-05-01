from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import Role as RoleEnum
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Employee, InternTravelExpense, User
from app.schemas.employee import (
    InternExpenseCreate,
    InternExpenseDecision,
    InternExpenseOut,
)
from app.services.employee_service import get_self_employee

router = APIRouter(prefix="/interns/expenses", tags=["intern-expenses"])


async def _self_intern(db: AsyncSession, user: User) -> Employee:
    emp = await get_self_employee(db, user)
    if not emp:
        raise ForbiddenError("No employee record linked to this account")
    if not emp.category or emp.category.code != "INTERN":
        raise ForbiddenError("Only interns can use this endpoint")
    return emp


def _is_approver(user: User) -> bool:
    approvers = {
        RoleEnum.HR.value,
        RoleEnum.MANAGER.value,
        RoleEnum.ADMIN.value,
        RoleEnum.DIRECTOR.value,
        RoleEnum.SUPER_ADMIN.value,
    }
    return bool(set(user.role_codes) & approvers)


@router.post("", response_model=InternExpenseOut, status_code=status.HTTP_201_CREATED)
async def submit_expense(
    payload: InternExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InternTravelExpense:
    intern = await _self_intern(db, user)

    # Cap by template's travel_expense_max if set.
    if intern.salary_template and intern.salary_template.travel_expense_max:
        cap = intern.salary_template.travel_expense_max
        if payload.amount > cap:
            raise ValidationError(
                f"Amount exceeds the monthly cap of ₹{cap:.0f}"
            )

    expense = InternTravelExpense(
        employee_id=intern.id,
        expense_date=payload.expense_date,
        expense_type=payload.expense_type,
        amount=payload.amount,
        receipt_url=payload.receipt_url,
        description=payload.description,
        status="pending",
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.get("/me", response_model=list[InternExpenseOut])
async def list_my_expenses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    intern = await _self_intern(db, user)
    stmt = (
        select(InternTravelExpense)
        .where(InternTravelExpense.employee_id == intern.id)
        .order_by(InternTravelExpense.expense_date.desc())
    )
    if status_filter:
        stmt = stmt.where(InternTravelExpense.status == status_filter)
    return (await db.execute(stmt)).scalars().all()


@router.get("/pending", response_model=list[InternExpenseOut])
async def list_pending(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _is_approver(user):
        raise ForbiddenError("Only HR/Manager/Admin can view pending expenses")
    return (
        await db.execute(
            select(InternTravelExpense)
            .where(InternTravelExpense.status == "pending")
            .order_by(InternTravelExpense.created_at.desc())
        )
    ).scalars().all()


@router.post("/{expense_id}/approve", response_model=InternExpenseOut)
async def approve_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InternTravelExpense:
    if not _is_approver(user):
        raise ForbiddenError("Only HR/Manager/Admin can approve")
    exp = (
        await db.execute(
            select(InternTravelExpense).where(InternTravelExpense.id == expense_id)
        )
    ).scalar_one_or_none()
    if not exp:
        raise NotFoundError("Expense not found")
    if exp.status != "pending":
        raise ValidationError("Only pending expenses can be approved")
    exp.status = "approved"
    exp.approved_by = user.id
    exp.approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(exp)
    return exp


@router.post("/{expense_id}/reject", response_model=InternExpenseOut)
async def reject_expense(
    expense_id: int,
    payload: InternExpenseDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InternTravelExpense:
    if not _is_approver(user):
        raise ForbiddenError("Only HR/Manager/Admin can reject")
    exp = (
        await db.execute(
            select(InternTravelExpense).where(InternTravelExpense.id == expense_id)
        )
    ).scalar_one_or_none()
    if not exp:
        raise NotFoundError("Expense not found")
    if exp.status != "pending":
        raise ValidationError("Only pending expenses can be rejected")
    exp.status = "rejected"
    exp.approved_by = user.id
    exp.approved_at = datetime.now(timezone.utc)
    exp.rejection_reason = payload.rejection_reason
    await db.commit()
    await db.refresh(exp)
    return exp


@router.post("/{expense_id}/reimburse", response_model=InternExpenseOut)
async def mark_reimbursed(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
) -> InternTravelExpense:
    exp = (
        await db.execute(
            select(InternTravelExpense).where(InternTravelExpense.id == expense_id)
        )
    ).scalar_one_or_none()
    if not exp:
        raise NotFoundError("Expense not found")
    if exp.status != "approved":
        raise ValidationError("Only approved expenses can be reimbursed")
    exp.status = "reimbursed"
    exp.reimbursed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(exp)
    return exp


@router.get("/report", response_model=list[InternExpenseOut])
async def report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _is_approver(user):
        raise ForbiddenError("Only HR/Admin can view the report")
    return (
        await db.execute(
            select(InternTravelExpense).order_by(
                InternTravelExpense.expense_date.desc()
            )
        )
    ).scalars().all()

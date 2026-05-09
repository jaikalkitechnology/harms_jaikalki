from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import require_permission, require_super_admin
from app.dependencies import get_current_user, get_db
from app.models import Employee, SalaryTemplate, User
from app.schemas.employee import (
    SalaryBreakupOut,
    SalaryTemplateCreate,
    SalaryTemplateOut,
    SalaryTemplateUpdate,
)
from app.services.salary_calculator import JaikalkiSalaryCalculator

router = APIRouter(prefix="/salary-templates", tags=["salary-templates"])


@router.get("", response_model=list[SalaryTemplateOut])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    category: Optional[str] = Query(default=None),
    active_only: bool = True,
) -> list[SalaryTemplate]:
    stmt = select(SalaryTemplate).order_by(SalaryTemplate.designation_level)
    if category:
        stmt = stmt.where(SalaryTemplate.category == category)
    if active_only:
        stmt = stmt.where(SalaryTemplate.is_active.is_(True))
    return (await db.execute(stmt)).scalars().all()


@router.get("/{template_id}", response_model=SalaryTemplateOut)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SalaryTemplate:
    t = (
        await db.execute(select(SalaryTemplate).where(SalaryTemplate.id == template_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Salary template not found")
    return t


@router.post(
    "",
    response_model=SalaryTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    body: SalaryTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
) -> SalaryTemplate:
    if (
        await db.execute(
            select(SalaryTemplate).where(SalaryTemplate.template_code == body.template_code)
        )
    ).scalar_one_or_none():
        raise ConflictError("template_code already exists")
    obj = SalaryTemplate(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/{template_id}", response_model=SalaryTemplateOut)
async def update_template(
    template_id: int,
    body: SalaryTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
) -> SalaryTemplate:
    obj = (
        await db.execute(select(SalaryTemplate).where(SalaryTemplate.id == template_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Salary template not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
) -> None:
    """Hard delete falls back to soft-delete (is_active=false) if the
    template is referenced by an employee."""
    obj = (
        await db.execute(select(SalaryTemplate).where(SalaryTemplate.id == template_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Salary template not found")
    try:
        await db.delete(obj)
        await db.commit()
    except Exception:
        await db.rollback()
        obj.is_active = False
        await db.commit()


@router.get("/{template_id}/calculate", response_model=SalaryBreakupOut)
async def calculate(
    template_id: int,
    ctc: Optional[Decimal] = Query(default=None, description="Optional CTC override"),
    employee_id: Optional[int] = Query(
        default=None,
        description="If provided, applies that employee's statutory overrides (PF opt-out, PT state, etc.)",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("salary.view.team")),
) -> dict:
    t = (
        await db.execute(select(SalaryTemplate).where(SalaryTemplate.id == template_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Salary template not found")

    emp: Optional[Employee] = None
    if employee_id is not None:
        emp = (
            await db.execute(select(Employee).where(Employee.id == employee_id))
        ).scalar_one_or_none()

    calc = JaikalkiSalaryCalculator()
    return calc.calculate(t, ctc_annual=ctc, employee=emp).as_dict()

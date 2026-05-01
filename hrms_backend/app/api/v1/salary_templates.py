from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission, require_super_admin
from app.dependencies import get_current_user, get_db
from app.models import SalaryTemplate, User
from app.schemas.employee import SalaryBreakupOut, SalaryTemplateOut
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


@router.get("/{template_id}/calculate", response_model=SalaryBreakupOut)
async def calculate(
    template_id: int,
    ctc: Optional[Decimal] = Query(default=None, description="Optional CTC override"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("salary.view.team")),
) -> dict:
    t = (
        await db.execute(select(SalaryTemplate).where(SalaryTemplate.id == template_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Salary template not found")

    calc = JaikalkiSalaryCalculator()
    return calc.calculate(t, ctc_annual=ctc).as_dict()

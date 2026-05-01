from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Department, Designation, EmployeeCategory, User
from app.schemas.employee import (
    CategoryOut,
    DepartmentCreate,
    DepartmentOut,
    DesignationCreate,
    DesignationOut,
)

router = APIRouter(tags=["organization"])


# ── Categories ─────────────────────────────────────────────────────────
@router.get("/employee-categories", response_model=list[CategoryOut])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        await db.execute(select(EmployeeCategory).order_by(EmployeeCategory.id))
    ).scalars().all()


# ── Departments ────────────────────────────────────────────────────────
@router.get("/departments", response_model=list[DepartmentOut])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        await db.execute(select(Department).order_by(Department.name))
    ).scalars().all()


@router.post(
    "/departments",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = Department(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Designations ──────────────────────────────────────────────────────
@router.get("/designations", response_model=list[DesignationOut])
async def list_designations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        await db.execute(select(Designation).order_by(Designation.level.desc(), Designation.name))
    ).scalars().all()


@router.post(
    "/designations",
    response_model=DesignationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_designation(
    payload: DesignationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = Designation(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/designations/{designation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_designation(
    designation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Designation).where(Designation.id == designation_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Designation not found")
    await db.delete(obj)
    await db.commit()

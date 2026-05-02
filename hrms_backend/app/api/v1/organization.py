from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Department, Designation, EmployeeCategory, Shift, User
from app.schemas.attendance import ShiftOut
from app.schemas.employee import (
    CategoryOut,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    DesignationCreate,
    DesignationOut,
    DesignationUpdate,
    ShiftCreate,
    ShiftUpdate,
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


@router.put("/departments/{dept_id}", response_model=DepartmentOut)
async def update_department(
    dept_id: int,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Department).where(Department.id == dept_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Department not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/departments/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Department).where(Department.id == dept_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Department not found")
    await db.delete(obj)
    await db.commit()


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


@router.put("/designations/{designation_id}", response_model=DesignationOut)
async def update_designation(
    designation_id: int,
    payload: DesignationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Designation).where(Designation.id == designation_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Designation not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
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


# ── Shifts ─────────────────────────────────────────────────────────────
@router.get("/shifts", response_model=list[ShiftOut])
async def list_shifts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        await db.execute(select(Shift).order_by(Shift.start_time))
    ).scalars().all()


@router.post(
    "/shifts",
    response_model=ShiftOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_shift(
    payload: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    if payload.is_default:
        # Only one default at a time.
        for row in (await db.execute(select(Shift))).scalars().all():
            if row.is_default:
                row.is_default = False
    obj = Shift(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/shifts/{shift_id}", response_model=ShiftOut)
async def update_shift(
    shift_id: int,
    payload: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Shift).where(Shift.id == shift_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Shift not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default") is True:
        for row in (await db.execute(select(Shift).where(Shift.id != shift_id))).scalars().all():
            if row.is_default:
                row.is_default = False
    for k, v in data.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(select(Shift).where(Shift.id == shift_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Shift not found")
    await db.delete(obj)
    await db.commit()

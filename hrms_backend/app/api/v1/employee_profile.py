"""Employee profile auxiliaries: photo, passport, family, nominees."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import (
    Employee,
    EmployeeNominee,
    EmployeePassport,
    FamilyMember,
    User,
)
from app.schemas.employee import (
    FamilyMemberCreate,
    FamilyMemberOut,
    FamilyMemberUpdate,
    NomineeCreate,
    NomineeOut,
    NomineeUpdate,
    PassportOut,
    PassportUpsert,
)
from app.services import employee_service as svc
from app.services.storage import upload_fileobj

router = APIRouter(tags=["employee-profile"])

_PHOTO_MAX_BYTES = 5 * 1024 * 1024
_PHOTO_MIME = {"image/jpeg", "image/png", "image/webp"}


# ── Profile photo ───────────────────────────────────────────────────────
@router.post(
    "/employees/{employee_id}/photo",
    response_model=dict,
)
async def upload_photo(
    employee_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if file.content_type and file.content_type not in _PHOTO_MIME:
        raise ValidationError(
            f"Profile photo must be JPEG/PNG/WEBP (got {file.content_type})"
        )
    emp = await svc.get_employee(db, employee_id)
    can_edit = svc.can_see_all(user) or emp.user_id == user.id
    if not can_edit:
        raise ForbiddenError("Cannot upload photo for this employee")

    contents = await file.read()
    if len(contents) > _PHOTO_MAX_BYTES:
        raise ValidationError("Photo too large (max 5 MB)")

    import io

    _, url = upload_fileobj(
        io.BytesIO(contents),
        key_prefix=f"employees/{emp.employee_code}/photo",
        filename=file.filename or "photo.jpg",
        content_type=file.content_type,
    )
    emp.photo_url = url
    await db.commit()
    await db.refresh(emp)
    return {"photo_url": url}


# ── Passport / visa ────────────────────────────────────────────────────
@router.get("/employees/{employee_id}/passport", response_model=Optional[PassportOut])
async def get_passport(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await svc.get_employee(db, employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    return (
        await db.execute(
            select(EmployeePassport).where(EmployeePassport.employee_id == employee_id)
        )
    ).scalar_one_or_none()


@router.put("/employees/{employee_id}/passport", response_model=PassportOut)
async def upsert_passport(
    employee_id: int,
    payload: PassportUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    existing = (
        await db.execute(
            select(EmployeePassport).where(EmployeePassport.employee_id == employee_id)
        )
    ).scalar_one_or_none()
    data = payload.model_dump(exclude_unset=False)
    if existing is None:
        passport = EmployeePassport(employee_id=emp.id, **data)
        db.add(passport)
    else:
        passport = existing
        for k, v in data.items():
            setattr(passport, k, v)
    await db.commit()
    await db.refresh(passport)
    return passport


@router.delete(
    "/employees/{employee_id}/passport", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_passport(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    existing = (
        await db.execute(
            select(EmployeePassport).where(EmployeePassport.employee_id == employee_id)
        )
    ).scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()


# ── Nominees ───────────────────────────────────────────────────────────
@router.get("/employees/{employee_id}/nominees", response_model=list[NomineeOut])
async def list_nominees(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await svc.get_employee(db, employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    return (
        await db.execute(
            select(EmployeeNominee)
            .where(EmployeeNominee.employee_id == employee_id)
            .order_by(EmployeeNominee.nominee_type, EmployeeNominee.id)
        )
    ).scalars().all()


@router.post(
    "/employees/{employee_id}/nominees",
    response_model=NomineeOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_nominee(
    employee_id: int,
    payload: NomineeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    n = EmployeeNominee(employee_id=emp.id, **payload.model_dump())
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n


@router.put("/nominees/{nominee_id}", response_model=NomineeOut)
async def update_nominee(
    nominee_id: int,
    payload: NomineeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    n = (
        await db.execute(select(EmployeeNominee).where(EmployeeNominee.id == nominee_id))
    ).scalar_one_or_none()
    if not n:
        raise NotFoundError("Nominee not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(n, k, v)
    await db.commit()
    await db.refresh(n)
    return n


@router.delete("/nominees/{nominee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nominee(
    nominee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    n = (
        await db.execute(select(EmployeeNominee).where(EmployeeNominee.id == nominee_id))
    ).scalar_one_or_none()
    if n:
        await db.delete(n)
        await db.commit()


# ── Family ─────────────────────────────────────────────────────────────
@router.get(
    "/employees/{employee_id}/family", response_model=list[FamilyMemberOut]
)
async def list_family(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await svc.get_employee(db, employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    return (
        await db.execute(
            select(FamilyMember)
            .where(FamilyMember.employee_id == employee_id)
            .order_by(FamilyMember.id)
        )
    ).scalars().all()


@router.post(
    "/employees/{employee_id}/family",
    response_model=FamilyMemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_family(
    employee_id: int,
    payload: FamilyMemberCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    f = FamilyMember(employee_id=emp.id, **payload.model_dump())
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


@router.put("/family/{member_id}", response_model=FamilyMemberOut)
async def update_family(
    member_id: int,
    payload: FamilyMemberUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    f = (
        await db.execute(select(FamilyMember).where(FamilyMember.id == member_id))
    ).scalar_one_or_none()
    if not f:
        raise NotFoundError("Family member not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    await db.commit()
    await db.refresh(f)
    return f


@router.delete("/family/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    f = (
        await db.execute(select(FamilyMember).where(FamilyMember.id == member_id))
    ).scalar_one_or_none()
    if f:
        await db.delete(f)
        await db.commit()

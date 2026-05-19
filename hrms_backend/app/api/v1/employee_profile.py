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
    AttendanceCycle,
    Employee,
    EmployeeBankDetails,
    EmployeeNominee,
    EmployeePassport,
    FamilyMember,
    User,
)
from app.schemas.employee import (
    AttendanceCycleCreate,
    AttendanceCycleOut,
    AttendanceCycleUpdate,
    BankDetailsOut,
    BankDetailsUpsert,
    FamilyMemberCreate,
    FamilyMemberOut,
    FamilyMemberUpdate,
    MyStatutoryOut,
    MyStatutoryUpdate,
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


# ── Self-service statutory & nominees (mobile profile) ─────────────────
async def _require_self_employee(db: AsyncSession, user: User) -> Employee:
    emp = await svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


async def _list_nominees(db: AsyncSession, employee_id: int):
    return (
        await db.execute(
            select(EmployeeNominee)
            .where(EmployeeNominee.employee_id == employee_id)
            .order_by(EmployeeNominee.nominee_type, EmployeeNominee.id)
        )
    ).scalars().all()


@router.get("/employees/me/statutory", response_model=MyStatutoryOut)
async def my_statutory(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _require_self_employee(db, user)
    nominees = await _list_nominees(db, emp.id)
    return MyStatutoryOut(
        pf_number=emp.pf_number,
        uan_number=emp.uan_number,
        esic_number=emp.esic_number,
        insurance_company=emp.insurance_company,
        insurance_policy_no=emp.insurance_policy_no,
        nominees=[NomineeOut.model_validate(n) for n in nominees],
        nominees_locked=len(nominees) > 0,
    )


@router.put("/employees/me/statutory", response_model=MyStatutoryOut)
async def update_my_statutory(
    payload: MyStatutoryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add-only: the employee may fill a blank statutory field but cannot
    overwrite a value already on record (HR owns corrections)."""
    emp = await _require_self_employee(db, user)
    data = payload.model_dump(exclude_unset=True)
    for field in (
        "pf_number",
        "uan_number",
        "esic_number",
        "insurance_company",
        "insurance_policy_no",
    ):
        new_val = (data.get(field) or "").strip() if field in data else None
        if not new_val:
            continue
        current = (getattr(emp, field) or "").strip()
        if current:
            raise ValidationError(
                f"{field.replace('_', ' ')} is already on record — "
                "contact HR to change it."
            )
        setattr(emp, field, new_val)
    await db.commit()
    await db.refresh(emp)
    nominees = await _list_nominees(db, emp.id)
    return MyStatutoryOut(
        pf_number=emp.pf_number,
        uan_number=emp.uan_number,
        esic_number=emp.esic_number,
        insurance_company=emp.insurance_company,
        insurance_policy_no=emp.insurance_policy_no,
        nominees=[NomineeOut.model_validate(n) for n in nominees],
        nominees_locked=len(nominees) > 0,
    )


@router.post(
    "/employees/me/nominees",
    response_model=NomineeOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_my_nominee(
    payload: NomineeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Employees may add their own nominee(s) once. After any nominee
    exists the set is locked — further changes go through HR."""
    emp = await _require_self_employee(db, user)
    existing = await _list_nominees(db, emp.id)
    if existing:
        raise ForbiddenError(
            "Nominee details are locked. Contact HR to make changes."
        )
    n = EmployeeNominee(employee_id=emp.id, **payload.model_dump())
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n


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


# ── Bank account ──────────────────────────────────────────────────────
@router.get(
    "/employees/{employee_id}/bank", response_model=Optional[BankDetailsOut]
)
async def get_bank(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await svc.get_employee(db, employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    return (
        await db.execute(
            select(EmployeeBankDetails).where(
                EmployeeBankDetails.employee_id == employee_id
            )
        )
    ).scalar_one_or_none()


@router.put("/employees/{employee_id}/bank", response_model=BankDetailsOut)
async def upsert_bank(
    employee_id: int,
    payload: BankDetailsUpsert,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    existing = (
        await db.execute(
            select(EmployeeBankDetails).where(
                EmployeeBankDetails.employee_id == employee_id
            )
        )
    ).scalar_one_or_none()
    data = payload.model_dump()
    if existing is None:
        bank = EmployeeBankDetails(employee_id=emp.id, **data)
        db.add(bank)
    else:
        bank = existing
        for k, v in data.items():
            setattr(bank, k, v)
    await db.commit()
    await db.refresh(bank)
    return bank


@router.delete(
    "/employees/{employee_id}/bank", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_bank(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    existing = (
        await db.execute(
            select(EmployeeBankDetails).where(
                EmployeeBankDetails.employee_id == employee_id
            )
        )
    ).scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()


# ── Attendance cycles ─────────────────────────────────────────────────
DEFAULT_CYCLES = [
    ("CAL", "1st → last day (calendar month)", 1, True),
    ("C21_20", "21st of prev → 20th of current", 21, False),
    ("C26_25", "26th of prev → 25th of current", 26, False),
    ("C16_15", "16th of prev → 15th of current", 16, False),
]


async def _ensure_default_cycles(db: AsyncSession) -> None:
    existing = (
        await db.execute(select(AttendanceCycle))
    ).scalars().all()
    if existing:
        return
    for code, name, start_day, is_default in DEFAULT_CYCLES:
        db.add(
            AttendanceCycle(
                code=code,
                name=name,
                start_day=start_day,
                is_default=is_default,
                is_active=True,
            )
        )
    await db.commit()


@router.get("/attendance-cycles", response_model=list[AttendanceCycleOut])
async def list_cycles(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _ensure_default_cycles(db)
    stmt = select(AttendanceCycle).order_by(AttendanceCycle.start_day)
    if active_only:
        stmt = stmt.where(AttendanceCycle.is_active.is_(True))
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/attendance-cycles",
    response_model=AttendanceCycleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_cycle(
    payload: AttendanceCycleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    dup = (
        await db.execute(
            select(AttendanceCycle).where(AttendanceCycle.code == payload.code)
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise ValidationError(f"Cycle code {payload.code!r} already exists")
    c = AttendanceCycle(**payload.model_dump())
    db.add(c)
    if c.is_default:
        # Demote any other default.
        from sqlalchemy import update as sa_update

        await db.execute(
            sa_update(AttendanceCycle)
            .where(AttendanceCycle.code != payload.code)
            .values(is_default=False)
        )
    await db.commit()
    await db.refresh(c)
    return c


@router.put("/attendance-cycles/{cycle_id}", response_model=AttendanceCycleOut)
async def update_cycle(
    cycle_id: int,
    payload: AttendanceCycleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    c = (
        await db.execute(
            select(AttendanceCycle).where(AttendanceCycle.id == cycle_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise NotFoundError("Cycle not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    if c.is_default:
        from sqlalchemy import update as sa_update

        await db.execute(
            sa_update(AttendanceCycle)
            .where(AttendanceCycle.id != cycle_id)
            .values(is_default=False)
        )
    await db.commit()
    await db.refresh(c)
    return c


@router.delete(
    "/attendance-cycles/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_cycle(
    cycle_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    c = (
        await db.execute(
            select(AttendanceCycle).where(AttendanceCycle.id == cycle_id)
        )
    ).scalar_one_or_none()
    if not c:
        return
    # Refuse to delete a cycle that's still referenced by employees;
    # admin should retire it (`is_active=false`) or migrate the
    # employees first.
    in_use = (
        await db.execute(
            select(Employee.id)
            .where(Employee.attendance_cycle_start_day == c.start_day)
            .limit(1)
        )
    ).scalar_one_or_none()
    if in_use is not None:
        raise ValidationError(
            f"Cycle {c.code} is still in use; mark inactive instead of deleting."
        )
    await db.delete(c)
    await db.commit()

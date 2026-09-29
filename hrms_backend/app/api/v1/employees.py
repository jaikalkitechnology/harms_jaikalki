from typing import Optional, Sequence

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Employee, User
from app.schemas.employee import (
    CredentialActiveUpdate,
    CredentialCreate,
    CredentialOut,
    CredentialPasswordReset,
    EmployeeCreate,
    EmployeeListItem,
    EmployeeOut,
    EmployeeUpdate,
    ExpiringProbationItem,
    OrgChartNode,
    ProbationConfirmRequest,
    ProbationExtendRequest,
    ProbationOut,
)
from sqlalchemy import select
from app.services import employee_service as svc

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeListItem])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    search: Optional[str] = Query(default=None),
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    on_probation: Optional[bool] = None,
    limit: int = Query(default=100, le=500, ge=1),
    offset: int = Query(default=0, ge=0),
) -> Sequence[Employee]:
    return await svc.list_employees(
        db,
        user,
        search=search,
        department_id=department_id,
        category_id=category_id,
        on_probation=on_probation,
        limit=limit,
        offset=offset,
    )


@router.get("/me", response_model=EmployeeOut)
async def me(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Employee:
    emp = await svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


@router.get("/probation/expiring", response_model=list[ExpiringProbationItem])
async def list_expiring_probations(
    days: int = Query(default=15, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.view.all")),
) -> list[ExpiringProbationItem]:
    from datetime import date as _date
    rows = await svc.expiring_probations(db, days=days)
    today = _date.today()
    return [
        ExpiringProbationItem(
            employee_id=e.id,
            employee_code=e.employee_code,
            full_name=f"{e.first_name} {e.last_name}",
            probation_end_date=e.probation_end_date,
            days_remaining=(e.probation_end_date - today).days,
        )
        for e in rows
        if e.probation_end_date
    ]


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Employee:
    emp = await svc.get_employee(db, employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    return emp


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.create")),
) -> Employee:
    return await svc.create_employee(db, payload, user)


@router.put("/me", response_model=EmployeeOut)
async def update_self(
    payload: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Employee:
    emp = await svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    # Restrict the fields self-service can change.
    allowed = {"date_of_birth", "blood_group", "marital_status",
               "personal_email", "personal_phone", "photo_url"}
    filtered = payload.model_dump(exclude_unset=True)
    for k in list(filtered.keys()):
        if k not in allowed:
            filtered.pop(k)
    update = EmployeeUpdate(**filtered)
    return await svc.update_employee(db, emp, update)


@router.put("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
) -> Employee:
    emp = await svc.get_employee(db, employee_id)
    return await svc.update_employee(db, emp, payload)


# ── Credential management (mobile app login) ─────────────────────────
def _credential_to_out(user: Optional[User]) -> CredentialOut:
    if not user:
        return CredentialOut(user_id=0, email="", is_active=False, has_account=False)
    return CredentialOut(
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
        has_account=True,
    )


@router.get("/{employee_id}/credential", response_model=CredentialOut)
async def get_credential(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    if emp.user_id is None:
        return _credential_to_out(None)
    user = (
        await db.execute(select(User).where(User.id == emp.user_id))
    ).scalar_one_or_none()
    return _credential_to_out(user)


@router.post(
    "/{employee_id}/credential",
    response_model=CredentialOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    employee_id: int,
    payload: CredentialCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    """Create a mobile-app login for an existing employee. Admin must
    supply the initial password — the rep can change it from the app."""
    emp = await svc.get_employee(db, employee_id)
    user = await svc.create_user_account_for(
        db,
        employee=emp,
        email=payload.email,
        initial_password=payload.password,
        role_code=payload.role_code,
    )
    return _credential_to_out(user)


@router.post(
    "/{employee_id}/credential/password",
    response_model=CredentialOut,
)
async def reset_credential_password(
    employee_id: int,
    payload: CredentialPasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    user = await svc.reset_employee_password(
        db, employee=emp, new_password=payload.new_password
    )
    return _credential_to_out(user)


@router.post(
    "/{employee_id}/credential/active",
    response_model=CredentialOut,
)
async def set_credential_active(
    employee_id: int,
    payload: CredentialActiveUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    user = await svc.set_account_active(
        db, employee=emp, is_active=payload.is_active
    )
    return _credential_to_out(user)


@router.put("/{employee_id}/manager", response_model=EmployeeOut)
async def assign_manager(
    employee_id: int,
    manager_id: Optional[int],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
) -> Employee:
    emp = await svc.get_employee(db, employee_id)
    return await svc.assign_manager(db, emp, manager_id)


@router.post("/{employee_id}/confirm", response_model=ProbationOut)
async def confirm_employee(
    employee_id: int,
    payload: ProbationConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    return await svc.confirm_employee(
        db,
        emp,
        by_user=user,
        confirmation_letter_url=payload.confirmation_letter_url,
    )


@router.post("/{employee_id}/extend-probation", response_model=ProbationOut)
async def extend_probation(
    employee_id: int,
    payload: ProbationExtendRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    return await svc.extend_probation(
        db, emp, months=payload.months, reason=payload.reason
    )


@router.get("/org/chart", response_model=list[OrgChartNode])
async def get_org_chart(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    return await svc.org_chart(db)


_ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/{employee_id}/photo", response_model=EmployeeOut)
async def upload_employee_photo(
    employee_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Employee:
    """Upload a profile photo. Employees can update their own; HR/admin
    any employee."""
    emp = await svc.get_employee(db, employee_id)
    self_emp = await svc.get_self_employee(db, user)
    is_self = self_emp is not None and self_emp.id == emp.id
    if not is_self and not (
        set(user.role_codes)
        & {"super_admin", "director", "hr", "admin"}
    ):
        raise ForbiddenError("Cannot update another employee's photo")

    if file.content_type not in _ALLOWED_PHOTO_TYPES:
        from app.core.exceptions import ValidationError

        raise ValidationError("Only JPEG/PNG/WEBP images are allowed")

    content = await file.read()
    if len(content) > _MAX_PHOTO_BYTES:
        from app.core.exceptions import ValidationError

        raise ValidationError("Photo must be ≤ 5 MB")

    import io

    from app.services.storage import upload_fileobj

    _, url = upload_fileobj(
        io.BytesIO(content),
        key_prefix=f"profile-photos/{emp.employee_code}",
        filename=file.filename or "photo.jpg",
        content_type=file.content_type,
    )
    emp.photo_url = url
    await db.commit()
    await db.refresh(emp)
    return emp


# ── Onboarding lifecycle (Intern → Probation → Confirmation) ────────
from app.services import lifecycle_service
from app.schemas.employee import (
    LifecycleConfirmRequest,
    LifecycleExtendRequest,
    LifecyclePhaseOut,
    LifecycleStartRequest,
    LifecycleStateOut,
)


@router.get(
    "/{employee_id}/lifecycle",
    response_model=LifecycleStateOut,
)
async def get_lifecycle(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.view.all")),
):
    emp = await svc.get_employee(db, employee_id)
    stage = await lifecycle_service.stage_of(db, emp)
    history = await lifecycle_service.list_history(db, employee_id=employee_id)
    return LifecycleStateOut(
        employee_id=emp.id,
        stage=stage,
        is_on_probation=bool(emp.is_on_probation),
        confirmation_date=emp.confirmation_date,
        history=[LifecyclePhaseOut.model_validate(h) for h in history],
    )


@router.post(
    "/{employee_id}/lifecycle/intern/start",
    response_model=LifecyclePhaseOut,
)
async def start_intern(
    employee_id: int,
    payload: LifecycleStartRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    return await lifecycle_service.start_intern(
        db,
        employee=emp,
        start_date=payload.start_date,
        months=payload.months or lifecycle_service.DEFAULT_INTERN_MONTHS,
    )


@router.post(
    "/{employee_id}/lifecycle/intern/extend",
    response_model=LifecyclePhaseOut,
)
async def extend_intern(
    employee_id: int,
    payload: LifecycleExtendRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    return await lifecycle_service.extend_intern(
        db,
        employee=emp,
        extension_end=payload.extension_end_date,
        reason=payload.reason,
    )


@router.post(
    "/{employee_id}/lifecycle/probation/start",
    response_model=LifecyclePhaseOut,
)
async def start_probation(
    employee_id: int,
    payload: LifecycleStartRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    return await lifecycle_service.start_probation(
        db,
        employee=emp,
        start_date=payload.start_date,
        months=payload.months or lifecycle_service.DEFAULT_PROBATION_MONTHS,
    )


@router.post(
    "/{employee_id}/lifecycle/probation/extend",
    response_model=LifecyclePhaseOut,
)
async def extend_probation(
    employee_id: int,
    payload: LifecycleExtendRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    emp = await svc.get_employee(db, employee_id)
    return await lifecycle_service.extend_probation(
        db,
        employee=emp,
        extension_end=payload.extension_end_date,
        reason=payload.reason,
    )


@router.post(
    "/{employee_id}/lifecycle/confirm",
    response_model=LifecyclePhaseOut,
)
async def confirm_employee(
    employee_id: int,
    payload: LifecycleConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    from datetime import date as _date

    emp = await svc.get_employee(db, employee_id)
    return await lifecycle_service.confirm(
        db,
        employee=emp,
        confirmed_on=payload.confirmed_on or _date.today(),
        actor=user,
    )

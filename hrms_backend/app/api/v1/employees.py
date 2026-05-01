from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Employee, User
from app.schemas.employee import (
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

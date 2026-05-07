from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Employee, User
from app.schemas.verification import (
    FraudFlagCreate,
    FraudFlagOut,
    TatStat,
    TemplateCreate,
    TemplateOut,
    TemplateUpdate,
    VerificationAuditDecision,
    VerificationCreate,
    VerificationOut,
    VerificationSubmit,
    VerificationUpdate,
)
from app.services import employee_service as emp_svc
from app.services import verification_service as v_svc
from app.services.verification_pdf import render_verification_report

router = APIRouter(prefix="/verification", tags=["verification"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ─── Templates ────────────────────────────────────────────────────────
@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(
    search: Optional[str] = None,
    type_: Optional[str] = Query(default=None, alias="type"),
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await v_svc.list_templates(
        db,
        active_only=not include_inactive,
        search=search,
        type_=type_,
    )


@router.post(
    "/templates",
    response_model=TemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    payload: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await v_svc.create_template(db, payload=payload.model_dump())


@router.get("/templates/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await v_svc.get_template(db, template_id)


@router.put("/templates/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: int,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await v_svc.update_template(
        db, template_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    await v_svc.delete_template(db, template_id)


# ─── Verifications ────────────────────────────────────────────────────
@router.get("/", response_model=list[VerificationOut])
async def list_verifications(
    mine: bool = False,
    job_status: Optional[str] = Query(default=None, alias="status"),
    type_: Optional[str] = Query(default=None, alias="type"),
    search: Optional[str] = None,
    fraud_only: bool = False,
    assigned_to: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if mine:
        emp = await _self_employee(db, user)
        assigned_to = emp.id
    return await v_svc.list_verifications(
        db,
        assigned_to=assigned_to,
        status=job_status,
        type_=type_,
        search=search,
        fraud_only=fraud_only,
    )


@router.post(
    "/",
    response_model=VerificationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_verification(
    payload: VerificationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await v_svc.create_verification(db, payload=payload.model_dump())


@router.get("/queue", response_model=list[VerificationOut])
async def my_queue(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await v_svc.list_verifications(
        db, assigned_to=emp.id, status=None
    )


@router.get("/audit-queue", response_model=list[VerificationOut])
async def audit_queue(
    search: Optional[str] = None,
    type_: Optional[str] = Query(default=None, alias="type"),
    fraud_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await v_svc.list_verifications(
        db,
        status="audit_pending",
        search=search,
        type_=type_,
        fraud_only=fraud_only,
    )


@router.put("/{verification_id}", response_model=VerificationOut)
async def update_verification(
    verification_id: int,
    payload: VerificationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await v_svc.update_verification(
        db, verification_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.get("/tat-stats", response_model=TatStat)
async def get_tat_stats(
    mine: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    assigned_to = None
    if mine:
        emp = await _self_employee(db, user)
        assigned_to = emp.id
    return await v_svc.tat_stats(db, assigned_to=assigned_to)


@router.get("/{verification_id}", response_model=VerificationOut)
async def get_verification(
    verification_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await v_svc.get_verification(db, verification_id)


@router.post(
    "/{verification_id}/start", response_model=VerificationOut
)
async def start(
    verification_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await v_svc.start_verification(db, verification_id, employee=emp)


@router.post(
    "/{verification_id}/submit", response_model=VerificationOut
)
async def submit(
    verification_id: int,
    payload: VerificationSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await v_svc.submit_verification(
        db, verification_id, employee=emp, payload=payload.model_dump()
    )


@router.post(
    "/{verification_id}/audit", response_model=VerificationOut
)
async def audit(
    verification_id: int,
    payload: VerificationAuditDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    return await v_svc.audit_verification(
        db,
        verification_id,
        auditor=user,
        audit_status=payload.audit_status,
        audit_comments=payload.audit_comments,
    )


@router.post(
    "/{verification_id}/fraud-flag",
    response_model=FraudFlagOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_fraud_flag(
    verification_id: int,
    payload: FraudFlagCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    return await v_svc.add_fraud_flag(
        db,
        verification_id,
        auditor=user,
        flag_type=payload.flag_type,
        severity=payload.severity,
        notes=payload.notes,
    )


@router.get("/{verification_id}/report")
async def get_report_pdf(
    verification_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    v = await v_svc.get_verification(db, verification_id)
    template = await v_svc.get_template(db, v.template_id)
    verifier = None
    if v.assigned_to:
        verifier = (
            await db.execute(select(Employee).where(Employee.id == v.assigned_to))
        ).scalar_one_or_none()
    pdf = render_verification_report(
        verification=v, template=template, verifier=verifier
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{v.ticket_number.replace("/", "-")}.pdf"'
            )
        },
    )

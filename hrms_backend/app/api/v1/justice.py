from datetime import date, datetime
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import Role as RoleEnum
from app.dependencies import get_current_user, get_db
from app.models import (
    IccMember,
    JusticeAccessLog,
    JusticeComplaint,
    PoshAnnualReport,
    RetaliationFlag,
    User,
)
from app.schemas.justice import (
    ActionCreate,
    ActionOut,
    AssignRequest,
    ComplaintCreate,
    ComplaintDetail,
    ComplaintListItem,
    IccComplianceStatus,
    IccMemberCreate,
    IccMemberOut,
    PoshAnnualReportOut,
    ResolveRequest,
    RetaliationFlagCreate,
    RetaliationFlagOut,
    TimelineOut,
    WithdrawRequest,
)
from app.services import employee_service as emp_svc
from app.services import justice_service as svc

router = APIRouter(prefix="/justice", tags=["justice"])


def _can_act_authority(user: User) -> bool:
    return bool(
        set(user.role_codes)
        & {
            RoleEnum.DIRECTOR.value,
            RoleEnum.HR.value,
            RoleEnum.SUPER_ADMIN.value,
            RoleEnum.ADMIN.value,
        }
    )


def _is_super(user: User) -> bool:
    return RoleEnum.SUPER_ADMIN.value in user.role_codes


def _list_item(c: JusticeComplaint) -> ComplaintListItem:
    return ComplaintListItem(
        id=c.id,
        ticket_number=c.ticket_number,
        complaint_type=c.complaint_type,
        privacy_level=c.privacy_level,
        severity=c.severity,
        status=c.status,
        subject=c.subject,
        submitted_at=c.submitted_at,
        deadline_at=c.deadline_at,
        is_anonymous=c.privacy_level == "anonymous",
    )


def _detail(
    c: JusticeComplaint, decrypted: dict, access_log: Sequence[JusticeAccessLog]
) -> ComplaintDetail:
    return ComplaintDetail(
        id=c.id,
        ticket_number=c.ticket_number,
        complaint_type=c.complaint_type,
        privacy_level=c.privacy_level,
        severity=c.severity,
        status=c.status,
        subject=c.subject,
        description=decrypted["description"],
        desired_outcome=decrypted["desired_outcome"],
        incident_date=c.incident_date,
        incident_location=c.incident_location,
        submitted_at=c.submitted_at,
        acknowledged_at=c.acknowledged_at,
        resolved_at=c.resolved_at,
        deadline_at=c.deadline_at,
        assigned_to=c.assigned_to,
        complainant_employee_id=c.complainant_employee_id,
        accused=decrypted["accused"],
        witnesses=decrypted["witnesses"],
        evidence=decrypted["evidence"],
        actions=decrypted["actions"],
        timeline=[TimelineOut.model_validate(t) for t in c.timeline],
        access_log=[
            {
                "id": a.id,
                "user_id": a.user_id,
                "action": a.action,
                "timestamp": a.timestamp,
                "ip_address": a.ip_address,
            }
            for a in access_log
        ],
    )


# ── Submit ────────────────────────────────────────────────────────────
@router.post("/submit", response_model=ComplaintDetail, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    payload: ComplaintCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)

    c = await svc.submit_complaint(
        db,
        user=user,
        complainant_employee_id=emp.id if emp else None,
        complaint_type=payload.complaint_type,
        privacy_level=payload.privacy_level,
        severity=payload.severity,
        subject=payload.subject,
        description=payload.description,
        desired_outcome=payload.desired_outcome,
        incident_date=payload.incident_date,
        incident_location=payload.incident_location,
        accused=[a.model_dump() for a in payload.accused],
        witnesses=[w.model_dump() for w in payload.witnesses],
        evidence=[e.model_dump() for e in payload.evidence],
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    decrypted = svc.decrypt_complaint_view(c)
    log = (
        await db.execute(
            select(JusticeAccessLog)
            .where(JusticeAccessLog.complaint_id == c.id)
            .order_by(JusticeAccessLog.timestamp.desc())
        )
    ).scalars().all()
    return _detail(c, decrypted, log)


# ── My complaints ─────────────────────────────────────────────────────
@router.get("/me", response_model=list[ComplaintListItem])
async def list_mine(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        return []
    rows = await svc.list_my_complaints(db, emp.id)
    return [_list_item(c) for c in rows]


@router.get("/me/{complaint_id}", response_model=ComplaintDetail)
async def get_mine(
    complaint_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await emp_svc.get_self_employee(db, user)
    c = (
        await db.execute(
            select(JusticeComplaint).where(JusticeComplaint.id == complaint_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise NotFoundError("Complaint not found")
    if c.privacy_level != "open" or (
        not emp or c.complainant_employee_id != emp.id
    ):
        raise ForbiddenError(
            "Anonymous and confidential complaints can only be inspected by authorised users"
        )
    await svc.log_access(
        db, c.id, user.id, "view:self",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    decrypted = svc.decrypt_complaint_view(c)
    log = (
        await db.execute(
            select(JusticeAccessLog)
            .where(JusticeAccessLog.complaint_id == c.id)
            .order_by(JusticeAccessLog.timestamp.desc())
        )
    ).scalars().all()
    return _detail(c, decrypted, log)


# ── Authority inbox + detail ─────────────────────────────────────────
@router.get("/inbox", response_model=list[ComplaintListItem])
async def authority_inbox(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not (_can_act_authority(user) or await svc._is_icc_member(db, user)):
        raise ForbiddenError("Not authorised to view the justice inbox")
    rows = await svc.list_authority_inbox(db, user=user)
    return [_list_item(c) for c in rows]


@router.get("/{complaint_id}", response_model=ComplaintDetail)
async def get_complaint(
    complaint_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await svc.get_complaint(
        db,
        complaint_id,
        user=user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    decrypted = svc.decrypt_complaint_view(c)
    log = (
        await db.execute(
            select(JusticeAccessLog)
            .where(JusticeAccessLog.complaint_id == c.id)
            .order_by(JusticeAccessLog.timestamp.desc())
        )
    ).scalars().all()
    return _detail(c, decrypted, log)


@router.post("/{complaint_id}/assign", response_model=ComplaintListItem)
async def assign_complaint(
    complaint_id: int,
    payload: AssignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await svc.get_complaint(db, complaint_id, user=user, record_access=False)
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised to assign")
    c = await svc.assign_complaint(db, c, user=user, investigator_user_id=payload.user_id)
    return _list_item(c)


@router.post(
    "/{complaint_id}/action",
    response_model=ActionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_action(
    complaint_id: int,
    payload: ActionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await svc.get_complaint(db, complaint_id, user=user, record_access=False)
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised to record an action")
    action = await svc.add_action(
        db, c, user=user, action_type=payload.action_type, notes=payload.notes
    )
    from app.services import encryption as _enc
    return ActionOut(
        id=action.id,
        action_type=action.action_type,
        action_date=action.action_date,
        taken_by=action.taken_by,
        notes=_enc.decrypt(action.notes_encrypted),
    )


@router.post("/{complaint_id}/resolve", response_model=ComplaintListItem)
async def resolve_complaint(
    complaint_id: int,
    payload: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await svc.get_complaint(db, complaint_id, user=user, record_access=False)
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised to resolve")
    c = await svc.resolve_complaint(
        db, c, user=user, notes=payload.notes, action_type=payload.action_type
    )
    return _list_item(c)


@router.post("/me/{complaint_id}/withdraw", response_model=ComplaintListItem)
async def withdraw_complaint(
    complaint_id: int,
    payload: WithdrawRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = (
        await db.execute(
            select(JusticeComplaint).where(JusticeComplaint.id == complaint_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise NotFoundError("Complaint not found")
    emp = await emp_svc.get_self_employee(db, user)
    c = await svc.withdraw_complaint(
        db, c, user=user, employee_id=emp.id if emp else None, reason=payload.reason
    )
    return _list_item(c)


# ── POSH ──────────────────────────────────────────────────────────────
@router.get("/posh/cases", response_model=list[ComplaintListItem])
async def posh_cases(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not (
        _can_act_authority(user) or await svc._is_icc_member(db, user)
    ):
        raise ForbiddenError("Only ICC / Director / Super Admin can view POSH cases")
    rows = (
        await db.execute(
            select(JusticeComplaint)
            .where(
                JusticeComplaint.complaint_type.in_(["sexual_harassment", "discrimination"])
            )
            .order_by(JusticeComplaint.submitted_at.desc())
        )
    ).scalars().all()
    return [_list_item(c) for c in rows]


@router.get("/posh/annual-report", response_model=PoshAnnualReportOut)
async def posh_annual_report(
    year: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _can_act_authority(user):
        raise ForbiddenError("Not authorised")
    return await svc.generate_posh_annual_report(db, year=year, user=user)


# ── ICC management ────────────────────────────────────────────────────
@router.get("/icc/members", response_model=list[IccMemberOut])
async def list_icc_members(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised")
    stmt = select(IccMember).order_by(IccMember.role, IccMember.member_name)
    if active_only:
        stmt = stmt.where(IccMember.is_active.is_(True))
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/icc/members",
    response_model=IccMemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_icc_member(
    payload: IccMemberCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _is_super(user) and RoleEnum.HR.value not in user.role_codes:
        raise ForbiddenError("Only Super Admin / HR can manage ICC")
    obj = IccMember(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/icc/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_icc_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _is_super(user) and RoleEnum.HR.value not in user.role_codes:
        raise ForbiddenError("Only Super Admin / HR can manage ICC")
    obj = (
        await db.execute(select(IccMember).where(IccMember.id == member_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Member not found")
    obj.is_active = False
    await db.commit()


@router.get("/icc/compliance", response_model=IccComplianceStatus)
async def icc_compliance(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised")
    return await svc.icc_compliance(db)


# ── Retaliation flags ─────────────────────────────────────────────────
@router.post(
    "/retaliation",
    response_model=RetaliationFlagOut,
    status_code=status.HTTP_201_CREATED,
)
async def flag_retaliation(
    payload: RetaliationFlagCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised")
    obj = RetaliationFlag(
        complaint_id=payload.complaint_id,
        employee_id=payload.employee_id,
        flag_type=payload.flag_type,
        description=payload.description,
        detected_by=user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/retaliation", response_model=list[RetaliationFlagOut])
async def list_retaliation_flags(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _can_act_authority(user) and not await svc._is_icc_member(db, user):
        raise ForbiddenError("Not authorised")
    rows = (
        await db.execute(
            select(RetaliationFlag).order_by(RetaliationFlag.detected_at.desc())
        )
    ).scalars().all()
    return rows


# ── Resources page (helplines etc.) ───────────────────────────────────
@router.get("/resources")
async def resources(_: User = Depends(get_current_user)) -> dict:
    """Static helplines + policies surfaced to mobile clients."""
    return {
        "helplines": [
            {"name": "Women Helpline (India)", "number": "1091", "icon": "phone"},
            {"name": "National Emergency", "number": "112", "icon": "phone"},
            {"name": "Police", "number": "100", "icon": "phone"},
            {"name": "Cyber Crime", "number": "1930", "icon": "phone"},
        ],
        "policies": [
            {
                "title": "POSH Act 2013 — overview",
                "summary": (
                    "Sexual Harassment of Women at Workplace (Prevention, "
                    "Prohibition and Redressal) Act, 2013. Every employer "
                    "with 10+ employees must constitute an Internal "
                    "Complaints Committee (ICC) and resolve complaints "
                    "within 90 days."
                ),
            },
            {
                "title": "Confidentiality",
                "summary": (
                    "Disclosing the identity of a complainant or witness, "
                    "or the contents of a complaint, attracts a penalty of "
                    "₹5,000 under section 17 of the POSH Act."
                ),
            },
            {
                "title": "Anti-retaliation",
                "summary": (
                    "Adverse action against a complainant or witness "
                    "(transfer, demotion, performance hit, salary freeze "
                    "etc.) is treated as a fresh, separate violation."
                ),
            },
        ],
        "external_resources": [
            {
                "name": "She-Box (govt POSH portal)",
                "url": "https://shebox.wcd.gov.in/",
            },
            {
                "name": "Vishakha Guidelines (1997)",
                "url": "https://en.wikipedia.org/wiki/Vishakha_Guidelines",
            },
        ],
    }

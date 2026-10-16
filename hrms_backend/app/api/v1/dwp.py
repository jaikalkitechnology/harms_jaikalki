from datetime import date
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import DwpSubmission, DwpTemplate, Employee, User
from app.schemas.dwp import (
    DwpCommentCreate,
    DwpCommentOut,
    DwpStreakOut,
    DwpSubmissionFieldOut,
    DwpSubmissionOut,
    DwpSubmitRequest,
    DwpTeamSubmissionItem,
    DwpTemplateOut,
    DwpTemplateWithPrefill,
)
from app.services import dwp_service, employee_service as emp_svc

router = APIRouter(prefix="/dwp", tags=["dwp"])


async def _self_employee(db: AsyncSession, user: User) -> Employee:
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


def _serialize_submission(sub: DwpSubmission) -> DwpSubmissionOut:
    return DwpSubmissionOut(
        id=sub.id,
        employee_id=sub.employee_id,
        template_id=sub.template_id,
        type=sub.type,
        date=sub.date,
        submitted_at=sub.submitted_at,
        total_hours=sub.total_hours,
        mood_rating=sub.mood_rating,
        linked_morning_id=sub.linked_morning_id,
        fields=[
            DwpSubmissionFieldOut(
                field_key=f.field_key, value=f.value, file_url=f.file_url
            )
            for f in sub.fields
        ],
        comments=[DwpCommentOut.model_validate(c) for c in sub.comments],
    )


# ── Templates with prefill ─────────────────────────────────────────────
@router.get("/template/morning", response_model=DwpTemplateWithPrefill)
async def get_morning_template(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    template = await dwp_service.find_template(db, emp, type="morning")
    prefill, _ = await dwp_service.prefill_for(db, emp.id, type="morning")
    streak, _last = await dwp_service.streak_for(db, emp.id)
    return DwpTemplateWithPrefill(
        template=DwpTemplateOut.model_validate(template),
        prefill=prefill,
        streak_days=streak,
    )


@router.get("/template/eod", response_model=DwpTemplateWithPrefill)
async def get_eod_template(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    template = await dwp_service.find_template(db, emp, type="eod")
    prefill, linked = await dwp_service.prefill_for(db, emp.id, type="eod")
    streak, _last = await dwp_service.streak_for(db, emp.id)
    return DwpTemplateWithPrefill(
        template=DwpTemplateOut.model_validate(template),
        prefill=prefill,
        linked_morning_id=linked,
        streak_days=streak,
    )


# ── Submit ────────────────────────────────────────────────────────────
@router.post(
    "/morning/submit",
    response_model=DwpSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_morning(
    payload: DwpSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    tpl = (
        await db.execute(
            select(DwpTemplate).where(DwpTemplate.id == payload.template_id)
        )
    ).scalar_one_or_none()
    if not tpl:
        raise NotFoundError("Template not found")
    if tpl.type != "morning":
        from app.core.exceptions import ValidationError as VE
        raise VE("Template is not a morning template")
    sub = await dwp_service.submit(
        db,
        emp,
        template=tpl,
        fields=payload.fields,
        total_hours=payload.total_hours,
        mood_rating=payload.mood_rating,
        on_date=payload.on_date,
    )
    return _serialize_submission(sub)


@router.post(
    "/eod/submit",
    response_model=DwpSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_eod(
    payload: DwpSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    tpl = (
        await db.execute(
            select(DwpTemplate).where(DwpTemplate.id == payload.template_id)
        )
    ).scalar_one_or_none()
    if not tpl:
        raise NotFoundError("Template not found")
    if tpl.type != "eod":
        from app.core.exceptions import ValidationError as VE
        raise VE("Template is not an EOD template")
    sub = await dwp_service.submit(
        db,
        emp,
        template=tpl,
        fields=payload.fields,
        total_hours=payload.total_hours,
        mood_rating=payload.mood_rating,
        on_date=payload.on_date,
    )
    return _serialize_submission(sub)


# ── My submissions ────────────────────────────────────────────────────
@router.get("/me/today", response_model=list[DwpSubmissionOut])
async def my_today(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    rows = await dwp_service.my_history(
        db, emp.id, from_date=date.today(), to_date=date.today()
    )
    return [_serialize_submission(s) for s in rows]


@router.get("/me/history", response_model=list[DwpSubmissionOut])
async def my_history(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=60, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    rows = await dwp_service.my_history(
        db, emp.id, from_date=from_date, to_date=to_date, limit=limit
    )
    return [_serialize_submission(s) for s in rows]


@router.get("/employee/{employee_id}/history", response_model=list[DwpSubmissionOut])
async def employee_history(
    employee_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=30, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """A team member's daily plans, for anyone above them (and HR / Admin)."""
    team = await emp_svc.visible_employee_ids(db, user)
    if team is not None and employee_id not in team:
        raise NotFoundError("Employee not found")
    rows = await dwp_service.my_history(
        db, employee_id, from_date=from_date, to_date=to_date, limit=limit
    )
    return [_serialize_submission(s) for s in rows]


@router.get("/me/streak", response_model=DwpStreakOut)
async def my_streak(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    streak, last = await dwp_service.streak_for(db, emp.id)
    return DwpStreakOut(
        employee_id=emp.id, streak_days=streak, last_submission_date=last
    )


# ── Team views ────────────────────────────────────────────────────────
async def _visible_team_ids(
    db: AsyncSession, user: User
) -> Sequence[int] | None:
    visible = await emp_svc.visible_employee_ids(db, user)
    if visible is None:
        # No filter — see all (Director / HR / Admin).
        rows = (
            await db.execute(select(Employee.id).where(Employee.status == "active"))
        ).scalars().all()
        return rows
    return list(visible)


@router.get("/team/today", response_model=list[DwpTeamSubmissionItem])
async def team_today(
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await _can_act_on_team(db, user):
        raise ForbiddenError("Only managers / HR / Admin can view team DWP")
    ids = await _visible_team_ids(db, user)
    if not ids:
        return []
    subs = await dwp_service.team_today(
        db, employee_ids=ids, on_date=on_date
    )
    emp_rows = (
        await db.execute(select(Employee).where(Employee.id.in_({s.employee_id for s in subs})))
    ).scalars().all()
    by_id = {e.id: e for e in emp_rows}
    out = []
    for s in subs:
        e = by_id.get(s.employee_id)
        if not e:
            continue
        out.append(
            DwpTeamSubmissionItem(
                submission=_serialize_submission(s),
                employee_code=e.employee_code,
                employee_full_name=f"{e.first_name} {e.last_name}",
            )
        )
    return out


@router.get("/team/blockers", response_model=list[DwpTeamSubmissionItem])
async def team_blockers(
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await _can_act_on_team(db, user):
        raise ForbiddenError("Only managers / HR / Admin can view team blockers")
    ids = await _visible_team_ids(db, user)
    if not ids:
        return []
    subs = await dwp_service.team_blockers(
        db, employee_ids=ids, on_date=on_date
    )
    emp_rows = (
        await db.execute(
            select(Employee).where(Employee.id.in_({s.employee_id for s in subs}))
        )
    ).scalars().all()
    by_id = {e.id: e for e in emp_rows}
    out = []
    for s in subs:
        e = by_id.get(s.employee_id)
        if not e:
            continue
        out.append(
            DwpTeamSubmissionItem(
                submission=_serialize_submission(s),
                employee_code=e.employee_code,
                employee_full_name=f"{e.first_name} {e.last_name}",
            )
        )
    return out


async def _can_act_on_team(db: AsyncSession, user: User) -> bool:
    """Managers (by role, or anyone with people reporting to them) and
    HR / Admin / Director."""
    from app.core.permissions import Role as RoleEnum

    if set(user.role_codes) & {
        RoleEnum.MANAGER.value,
        RoleEnum.HR.value,
        RoleEnum.ADMIN.value,
        RoleEnum.DIRECTOR.value,
        RoleEnum.SUPER_ADMIN.value,
    }:
        return True
    return await emp_svc.has_reports(db, user)


# ── Comments ──────────────────────────────────────────────────────────
@router.post(
    "/{submission_id}/comment",
    response_model=DwpCommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    submission_id: int,
    payload: DwpCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await dwp_service.add_comment(
        db,
        submission_id=submission_id,
        user=user,
        comment=payload.comment,
        is_kudos=payload.is_kudos,
    )


# ── Admin: list / submit / edit / delete plans for any employee ──────
@router.get("/admin/templates")
async def admin_list_templates(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    """Active templates for the admin UI's plan editor."""
    rows = await dwp_service.list_active_templates(db)
    return [
        {
            "id": t.id,
            "type": t.type,
            "department_id": t.department_id,
            "fields": [
                {
                    "key": f.key,
                    "label": f.label,
                    "field_type": f.field_type,
                    "is_required": f.is_required,
                    "options": f.options,
                    "placeholder": f.placeholder,
                    "sort_order": f.sort_order,
                }
                for f in (t.fields or [])
            ],
        }
        for t in rows
    ]


class _AdminSubmit(BaseModel if False else object):  # type: ignore[misc]
    pass  # placeholder; we'll use a Pydantic model below


from pydantic import BaseModel as _BM  # noqa: E402

class AdminDwpSubmit(_BM):
    employee_id: int
    template_id: int
    fields: dict
    total_hours: Optional[float] = None
    mood_rating: Optional[int] = None
    on_date: Optional[date] = None


class AdminDwpUpdate(_BM):
    fields: Optional[dict] = None
    total_hours: Optional[float] = None
    mood_rating: Optional[int] = None


@router.post(
    "/admin/submit",
    response_model=DwpSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_submit(
    body: AdminDwpSubmit,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    tpl = (
        await db.execute(
            select(DwpTemplate).where(DwpTemplate.id == body.template_id)
        )
    ).scalar_one_or_none()
    if not tpl:
        raise NotFoundError("Template not found")
    from decimal import Decimal as _D
    sub = await dwp_service.admin_submit(
        db,
        employee_id=body.employee_id,
        template=tpl,
        fields=body.fields,
        total_hours=_D(str(body.total_hours)) if body.total_hours is not None else None,
        mood_rating=body.mood_rating,
        on_date=body.on_date,
    )
    return _serialize_submission(sub)


@router.put(
    "/admin/submissions/{submission_id}",
    response_model=DwpSubmissionOut,
)
async def admin_update_submission(
    submission_id: int,
    body: AdminDwpUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    from decimal import Decimal as _D
    sub = await dwp_service.update_submission(
        db,
        submission_id,
        fields=body.fields,
        total_hours=_D(str(body.total_hours)) if body.total_hours is not None else None,
        mood_rating=body.mood_rating,
    )
    return _serialize_submission(sub)


@router.delete(
    "/admin/submissions/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    await dwp_service.delete_submission(db, submission_id)


@router.get("/admin/submissions")
async def admin_list_submissions(
    employee_id: Optional[int] = None,
    type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    rows, total = await dwp_service.admin_list_submissions(
        db,
        employee_id=employee_id,
        type=type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        per_page=per_page,
    )
    return {
        "items": [_serialize_submission(s) for s in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }

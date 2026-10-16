"""My Team: managers see everyone below them, level by level; Director /
HR / Admin see the whole company. Salary stays out of these views."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models import Employee, LeaveRequest, LeaveType, User
from app.services import employee_service as emp_svc
from app.services import team_service as team

router = APIRouter(prefix="/team", tags=["team"])


async def _member(db: AsyncSession, user: User, employee_id: int) -> Employee:
    visible = await emp_svc.visible_employee_ids(db, user)
    if visible is not None and employee_id not in visible:
        raise NotFoundError("Employee not found")
    return await emp_svc.get_employee(db, employee_id)


@router.get("/me")
async def my_team_info(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Whether to show "My team" — and how big it is."""
    me = await emp_svc.get_self_employee(db, user)
    everyone = emp_svc.can_see_all(user)
    visible = await emp_svc.visible_employee_ids(db, user)

    async def current(ids: set[int]) -> int:
        if not ids:
            return 0
        return len(
            (
                await db.execute(
                    select(Employee.id).where(
                        Employee.id.in_(ids), Employee.status.not_in(team.LEFT)
                    )
                )
            ).all()
        )

    direct = await current(await emp_svc.subordinate_ids(db, me.id, depth=1)) if me else 0
    size = None if visible is None else await current(visible - ({me.id} if me else set()))
    return {
        "employee_id": me.id if me else None,
        "has_team": everyone or bool(size),
        "sees_everyone": everyone,
        "direct_count": direct,
        "team_size": size,
    }


@router.get("/overview")
async def team_overview(
    scope: str = Query(default="direct", pattern="^(direct|all)$"),
    root_id: Optional[int] = Query(default=None, description="Open someone's team"),
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    visible = await emp_svc.visible_employee_ids(db, user)
    if root_id is not None:
        root = await _member(db, user, root_id)
    elif visible is None:
        # Director / HR / Admin: from the top of the company — their own
        # team when they are the top.
        me = await emp_svc.get_self_employee(db, user)
        root = me if me and me.reporting_to is None else None
    else:
        root = await emp_svc.get_self_employee(db, user)
        if root is None:
            raise NotFoundError("No employee record linked to this account")
    return await team.overview(
        db, root=root, visible=visible, scope=scope, on=on_date or date.today()
    )


@router.get("/members/{employee_id}")
async def team_member(
    employee_id: int,
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """One person: who they report to, today's status, daily plan,
    target, recent leave and their own team's figures."""
    e = await _member(db, user, employee_id)
    on = on_date or date.today()
    me = await emp_svc.get_self_employee(db, user)
    direct = await emp_svc.visible_employee_ids(db, user, scope="direct")

    status = await team.day_status(db, [e.id], on)
    dwp = await team.dwp_status(db, [e.id], on)
    targets = await team.current_targets(db, [e.id], on)
    below = await emp_svc.subordinate_ids(db, e.id)
    below_active = set(
        (
            await db.execute(
                select(Employee.id).where(
                    Employee.id.in_(below or {-1}), Employee.status.not_in(team.LEFT)
                )
            )
        ).scalars()
    )
    from app.services.task_service import task_counts

    rollup = None
    if below_active:
        s = await team.day_status(db, below_active, on)
        d = await team.dwp_status(db, below_active, on)
        t = await team.current_targets(db, below_active, on)
        rollup = team.rollup(below_active, s, d, t, await task_counts(db, below_active))

    leaves = (
        await db.execute(
            select(LeaveRequest, LeaveType.name)
            .join(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
            .where(LeaveRequest.employee_id == e.id)
            .order_by(LeaveRequest.from_date.desc())
            .limit(8)
        )
    ).all()
    return {
        "employee_id": e.id,
        "employee_code": e.employee_code,
        "name": f"{e.first_name} {e.last_name}".strip(),
        "designation": e.designation.name if e.designation else None,
        "department": e.department.name if e.department else None,
        "photo_url": e.photo_url,
        "status": e.status,
        "date_of_joining": e.date_of_joining,
        "work_mode": e.work_mode,
        "work_location": e.work_location,
        "phone": e.personal_phone,
        "email": e.personal_email,
        "chain": await team.manager_chain(db, e, me.id if me else None),
        "is_direct_report": direct is None or e.id in direct,
        "on_date": on,
        "today": status[e.id],
        "dwp_morning": "morning" in dwp[e.id],
        "dwp_eod": "eod" in dwp[e.id],
        "target": targets.get(e.id),
        "tasks": (await task_counts(db, [e.id]))[e.id],
        "direct_reports": len(await emp_svc.subordinate_ids(db, e.id, depth=1)),
        "team": rollup,
        "recent_leaves": [
            {
                "id": r.id,
                "leave_type": name,
                "from_date": r.from_date,
                "to_date": r.to_date,
                "days": r.days,
                "status": r.status,
                "reason": r.reason,
            }
            for r, name in leaves
        ],
    }


@router.get("/org-chart")
async def org_chart(
    on_date: Optional[date] = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The reporting tree the caller may see — the whole company for
    Director / HR / Admin, otherwise the caller and everyone below — with
    today's status and team size on every node."""
    visible = await emp_svc.visible_employee_ids(db, user)
    staff = {
        e.id: e
        for e in (
            await db.execute(select(Employee).where(Employee.status.not_in(team.LEFT)))
        ).unique().scalars()
    }
    if visible is not None:
        staff = {i: e for i, e in staff.items() if i in visible}
    status = await team.day_status(db, staff, on_date or date.today())
    nodes = {
        i: {
            "employee_id": i,
            "employee_code": e.employee_code,
            "name": f"{e.first_name} {e.last_name}".strip(),
            "designation": e.designation.name if e.designation else None,
            "department": e.department.name if e.department else None,
            "photo_url": e.photo_url,
            "status_today": status[i]["status"],
            "children": [],
        }
        for i, e in staff.items()
    }
    roots = []
    for i, e in staff.items():
        parent = nodes.get(e.reporting_to)
        (parent["children"] if parent and e.reporting_to != i else roots).append(nodes[i])

    def finish(n: dict) -> int:
        n["children"].sort(key=lambda c: c["name"].lower())
        n["team_size"] = sum(1 + finish(c) for c in n["children"])
        return n["team_size"]

    for r in roots:
        finish(r)
    roots.sort(key=lambda r: (-r["team_size"], r["name"].lower()))
    return roots


# ── Team alerts (Settings → Team alerts) ─────────────────────────────
from pydantic import BaseModel  # noqa: E402

from app.core.exceptions import ValidationError  # noqa: E402
from app.core.permissions import require_permission  # noqa: E402
from app.services import team_alerts  # noqa: E402


class AlertSettings(BaseModel):
    morning_digest: Optional[bool] = None
    digest_time: Optional[str] = None
    plan_reminder: Optional[bool] = None
    plan_reminder_time: Optional[str] = None
    task_escalation: Optional[bool] = None
    escalate_after_days: Optional[int] = None
    weekly_summary: Optional[bool] = None
    weekly_day: Optional[int] = None
    weekly_time: Optional[str] = None
    target_alerts: Optional[bool] = None
    target_behind_by: Optional[int] = None
    incentive_auto_calc: Optional[bool] = None


@router.get("/alerts/settings")
async def get_alert_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    return await team_alerts.get_settings(db)


@router.put("/alerts/settings")
async def update_alert_settings(
    payload: AlertSettings,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    try:
        return await team_alerts.set_settings(db, payload.model_dump(exclude_unset=True), user)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.post("/alerts/run/{job}")
async def run_alert_now(
    job: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    """Send an alert now (outside its schedule)."""
    if job not in team_alerts.JOBS:
        raise NotFoundError("Unknown alert")
    result = await team_alerts.run_job(db, job)
    return {k: v for k, v in result.items() if k != "messages"}


@router.get("/alerts/preview")
async def preview_my_alerts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """What my morning digest and weekly summary would say right now
    (nothing is sent)."""
    me = await emp_svc.get_self_employee(db, user)
    if not me:
        return {"morning_digest": None, "weekly_summary": None}
    morning = await team_alerts.morning_digest(db, only=me.id, send=False)
    weekly = await team_alerts.weekly_summary(db, only=me.id, send=False, nudge=False)
    return {
        "morning_digest": (morning["messages"] or [None])[0],
        "weekly_summary": (weekly["messages"] or [None])[0],
    }

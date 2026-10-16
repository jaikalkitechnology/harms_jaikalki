"""Assigned tasks: a manager gives a task to someone below them (anyone
can note a task for themselves). The assignee updates progress; overdue
tasks are escalated up the reporting chain."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models import Employee, User, WorkTask, WorkTaskComment
from app.models.work_tasks import OPEN_STATUSES, TASK_PRIORITIES, TASK_STATUSES
from app.services import employee_service as emp_svc


def _now() -> datetime:
    return datetime.utcnow()


def _name(e: Optional[Employee]) -> str:
    return f"{e.first_name} {e.last_name}".strip() if e else ""


async def _employees(db: AsyncSession, ids: Iterable[Optional[int]]) -> dict[int, Employee]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {
        e.id: e
        for e in (await db.execute(select(Employee).where(Employee.id.in_(ids)))).unique().scalars()
    }


async def _push(
    db: AsyncSession, emp: Optional[Employee], *, type: str, title: str, body: str, data: dict
) -> None:
    """In-app + push to an employee's login (best effort)."""
    if not emp or not emp.user_id:
        return
    from app.services.notification_service import notify

    try:
        await notify(
            db, user_id=emp.user_id, type=type, title=title, body=body,
            data=data, send_push=True,
        )
    except Exception:  # pragma: no cover — push must never break the action
        await db.rollback()


# ── Access ───────────────────────────────────────────────────────────
class Access:
    """What the caller may do with tasks."""

    def __init__(self, user: User, me: Optional[Employee], team: Optional[set[int]]):
        self.user = user
        self.me = me
        self.team = team  # None = everyone

    @property
    def my_id(self) -> Optional[int]:
        return self.me.id if self.me else None

    def above(self, employee_id: int) -> bool:
        """Caller is HR / Admin / Director, or above this employee."""
        if self.team is None:
            return True
        return employee_id in self.team and employee_id != self.my_id

    def can_view(self, t: WorkTask) -> bool:
        return (
            t.assigned_to == self.my_id
            or t.assigned_by == self.my_id
            or t.created_by == self.user.id
            or self.above(t.assigned_to)
        )

    def can_manage(self, t: WorkTask) -> bool:
        """Edit details, reassign, cancel, delete."""
        return t.created_by == self.user.id or t.assigned_by == self.my_id or self.above(t.assigned_to)


async def access_for(db: AsyncSession, user: User) -> Access:
    return Access(
        user,
        await emp_svc.get_self_employee(db, user),
        await emp_svc.visible_employee_ids(db, user),
    )


async def _check_assignee(db: AsyncSession, acc: Access, employee_id: int) -> Employee:
    emp = await emp_svc.get_employee(db, employee_id)
    if employee_id != acc.my_id and not acc.above(employee_id):
        raise ForbiddenError("You can give tasks only to people in your team")
    if emp.status in ("resigned", "terminated", "separated", "inactive"):
        raise ValidationError(f"{_name(emp)} has left the company")
    return emp


# ── Serialise ────────────────────────────────────────────────────────
async def serialize(db: AsyncSession, tasks: list[WorkTask], acc: Access) -> list[dict]:
    people = await _employees(db, [t.assigned_to for t in tasks] + [t.assigned_by for t in tasks])
    counts = dict(
        (
            await db.execute(
                select(WorkTaskComment.task_id, func.count())
                .where(WorkTaskComment.task_id.in_([t.id for t in tasks] or [-1]))
                .group_by(WorkTaskComment.task_id)
            )
        ).all()
    )
    today = date.today()
    out = []
    for t in tasks:
        a = people.get(t.assigned_to)
        b = people.get(t.assigned_by)
        out.append(
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "assigned_to": t.assigned_to,
                "assignee_name": _name(a),
                "assignee_code": a.employee_code if a else None,
                "assigned_by": t.assigned_by,
                "assigner_name": _name(b) or None,
                "due_date": t.due_date,
                "priority": t.priority,
                "status": t.status,
                "is_overdue": bool(
                    t.due_date and t.due_date < today and t.status in OPEN_STATUSES
                ),
                "completed_at": t.completed_at,
                "completion_note": t.completion_note,
                "escalation_level": t.escalation_level,
                "comment_count": counts.get(t.id, 0),
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "can_manage": acc.can_manage(t),
                "is_mine": t.assigned_to == acc.my_id,
            }
        )
    return out


# ── Create / update ──────────────────────────────────────────────────
async def create_task(db: AsyncSession, acc: Access, payload: dict) -> WorkTask:
    assignee = await _check_assignee(db, acc, payload["assigned_to"])
    if payload.get("priority", "medium") not in TASK_PRIORITIES:
        raise ValidationError("Unknown priority")
    t = WorkTask(
        title=payload["title"].strip(),
        description=(payload.get("description") or "").strip() or None,
        assigned_to=assignee.id,
        assigned_by=acc.my_id,
        created_by=acc.user.id,
        due_date=payload.get("due_date"),
        priority=payload.get("priority") or "medium",
        status="open",
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    if assignee.id != acc.my_id:
        due = f" · due {t.due_date.strftime('%d %b')}" if t.due_date else ""
        await _push(
            db, assignee,
            type="task_assigned",
            title=f"New task: {t.title}",
            body=f"From {_name(acc.me) or acc.user.full_name}{due}",
            data={"task_id": t.id},
        )
    return t


async def get_task(db: AsyncSession, acc: Access, task_id: int) -> WorkTask:
    t = (await db.execute(select(WorkTask).where(WorkTask.id == task_id))).scalar_one_or_none()
    if not t or not acc.can_view(t):
        raise NotFoundError("Task not found")
    return t


async def update_task(db: AsyncSession, acc: Access, task_id: int, changes: dict) -> WorkTask:
    t = await get_task(db, acc, task_id)
    manage = acc.can_manage(t)
    detail_keys = {"title", "description", "due_date", "priority", "assigned_to"}
    if not manage and (set(changes) & detail_keys):
        raise ForbiddenError("Only the person who gave the task can change it")
    new_status = changes.get("status")
    if new_status is not None:
        if new_status not in TASK_STATUSES:
            raise ValidationError("Unknown status")
        if new_status == "cancelled" and not manage:
            raise ForbiddenError("Only the person who gave the task can cancel it")
    if "priority" in changes and changes["priority"] not in TASK_PRIORITIES:
        raise ValidationError("Unknown priority")

    old_assignee, old_status = t.assigned_to, t.status
    if "assigned_to" in changes and changes["assigned_to"] != t.assigned_to:
        await _check_assignee(db, acc, changes["assigned_to"])
    for k in ("title", "description", "due_date", "priority", "assigned_to", "completion_note"):
        if k in changes:
            v = changes[k]
            if k == "title":
                v = (v or "").strip()
                if len(v) < 2:
                    raise ValidationError("Give the task a title")
            setattr(t, k, v)
    if new_status is not None:
        t.status = new_status
        t.completed_at = _now() if new_status == "done" else None
    if "due_date" in changes:
        # A new deadline starts the escalation over.
        t.escalation_level = 0
        t.last_escalated_at = None
    await db.commit()
    await db.refresh(t)

    if new_status is not None and (new_status == "done") != (old_status == "done"):
        from app.services.sales_service import refresh_targets_for

        await refresh_targets_for(db, t.assigned_to)

    people = await _employees(db, [t.assigned_to, t.assigned_by])
    if t.assigned_to != old_assignee and t.assigned_to != acc.my_id:
        await _push(
            db, people.get(t.assigned_to),
            type="task_assigned",
            title=f"New task: {t.title}",
            body=f"From {_name(acc.me) or acc.user.full_name}",
            data={"task_id": t.id},
        )
    if new_status == "done" and old_status != "done" and t.assigned_by and t.assigned_by != acc.my_id:
        await _push(
            db, people.get(t.assigned_by),
            type="task_done",
            title=f"Done: {t.title}",
            body=f"{_name(people.get(t.assigned_to))} completed the task"
            + (f" — {t.completion_note}" if t.completion_note else ""),
            data={"task_id": t.id},
        )
    return t


async def delete_task(db: AsyncSession, acc: Access, task_id: int) -> None:
    t = await get_task(db, acc, task_id)
    if not acc.can_manage(t):
        raise ForbiddenError("Only the person who gave the task can delete it")
    await db.delete(t)
    await db.commit()


# ── Comments ─────────────────────────────────────────────────────────
async def list_comments(db: AsyncSession, acc: Access, task_id: int) -> list[WorkTaskComment]:
    await get_task(db, acc, task_id)
    return list(
        (
            await db.execute(
                select(WorkTaskComment)
                .where(WorkTaskComment.task_id == task_id)
                .order_by(WorkTaskComment.created_at, WorkTaskComment.id)
            )
        ).scalars()
    )


async def add_comment(db: AsyncSession, acc: Access, task_id: int, body: str) -> WorkTaskComment:
    t = await get_task(db, acc, task_id)
    body = (body or "").strip()
    if not body:
        raise ValidationError("Write a comment")
    c = WorkTaskComment(
        task_id=t.id,
        user_id=acc.user.id,
        author_name=_name(acc.me) or acc.user.full_name or acc.user.email,
        body=body[:4000],
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    # Tell the other side (assignee ⇄ assigner).
    people = await _employees(db, [t.assigned_to, t.assigned_by])
    for emp_id in {t.assigned_to, t.assigned_by} - {acc.my_id, None}:
        await _push(
            db, people.get(emp_id),
            type="task_comment",
            title=f"Comment on: {t.title}",
            body=f"{c.author_name}: {body[:120]}",
            data={"task_id": t.id},
        )
    return c


# ── Lists ────────────────────────────────────────────────────────────
def _status_filter(stmt, status: str):
    if status == "open":
        return stmt.where(WorkTask.status.in_(OPEN_STATUSES))
    if status == "overdue":
        return stmt.where(
            WorkTask.status.in_(OPEN_STATUSES), WorkTask.due_date < date.today()
        )
    if status in TASK_STATUSES:
        return stmt.where(WorkTask.status == status)
    return stmt  # "all"


def _order(stmt):
    # Open first, then by due date (no date last), newest first.
    return stmt.order_by(
        WorkTask.status.in_(OPEN_STATUSES).desc(),
        WorkTask.due_date.is_(None),
        WorkTask.due_date,
        WorkTask.id.desc(),
    )


async def list_tasks(
    db: AsyncSession,
    acc: Access,
    *,
    view: str,
    status: str = "open",
    employee_id: Optional[int] = None,
    scope: str = "all",
    limit: int = 300,
) -> list[WorkTask]:
    """view: "mine" (given to me) · "given" (I gave to others) · "team"
    (given to anyone below me — ``scope`` direct / all)."""
    stmt = select(WorkTask)
    if view == "mine":
        stmt = stmt.where(WorkTask.assigned_to == (acc.my_id or -1))
    elif view == "given":
        stmt = stmt.where(
            or_(WorkTask.assigned_by == (acc.my_id or -1), WorkTask.created_by == acc.user.id),
            WorkTask.assigned_to != (acc.my_id or -1),
        )
    else:
        if acc.team is None:
            ids = None
        elif scope == "direct" and acc.me:
            ids = await emp_svc.subordinate_ids(db, acc.me.id, depth=1)
        else:
            ids = acc.team - {acc.my_id}
        if ids is not None:
            stmt = stmt.where(WorkTask.assigned_to.in_(ids or {-1}))
        if employee_id is not None:
            if not acc.above(employee_id) and employee_id != acc.my_id:
                raise NotFoundError("Employee not found")
            stmt = stmt.where(WorkTask.assigned_to == employee_id)
    stmt = _order(_status_filter(stmt, status)).limit(limit)
    return list((await db.execute(stmt)).scalars())


async def task_counts(db: AsyncSession, employee_ids: Iterable[int]) -> dict[int, dict]:
    """employee id → {open, overdue, done_7d}."""
    ids = list(employee_ids)
    out = {i: {"open": 0, "overdue": 0, "done_7d": 0} for i in ids}
    if not ids:
        return out
    today = date.today()
    week_ago = _now() - timedelta(days=7)
    for emp_id, status, due, done_at in (
        await db.execute(
            select(WorkTask.assigned_to, WorkTask.status, WorkTask.due_date, WorkTask.completed_at)
            .where(WorkTask.assigned_to.in_(ids))
            .where(
                or_(
                    WorkTask.status.in_(OPEN_STATUSES),
                    WorkTask.completed_at >= week_ago,
                )
            )
        )
    ).all():
        c = out[emp_id]
        if status in OPEN_STATUSES:
            c["open"] += 1
            if due and due < today:
                c["overdue"] += 1
        elif status == "done" and done_at and done_at >= week_ago:
            c["done_7d"] += 1
    return out


# ── Escalation ───────────────────────────────────────────────────────
async def escalate_overdue(db: AsyncSession, *, after_days: int = 2) -> dict:
    """Run once a day. Day after the due date: remind the assignee and
    whoever gave the task. Then every ``after_days`` days, tell the next
    manager up the assignee's reporting chain."""
    today = date.today()
    tasks = list(
        (
            await db.execute(
                select(WorkTask).where(
                    WorkTask.status.in_(OPEN_STATUSES),
                    WorkTask.due_date.is_not(None),
                    WorkTask.due_date < today,
                )
            )
        ).scalars()
    )
    managers = dict(
        (await db.execute(select(Employee.id, Employee.reporting_to))).all()
    )
    sent = 0
    for t in tasks:
        days_late = (today - t.due_date).days
        if t.last_escalated_at and t.last_escalated_at.date() >= today:
            continue
        people = await _employees(db, [t.assigned_to, t.assigned_by])
        assignee = people.get(t.assigned_to)
        if assignee is None or assignee.status in ("resigned", "terminated", "separated", "inactive"):
            continue
        due = t.due_date.strftime("%d %b")
        if t.escalation_level == 0:
            await _push(
                db, assignee,
                type="task_overdue",
                title=f"Overdue: {t.title}",
                body=f"It was due {due}. Update it or ask for more time.",
                data={"task_id": t.id},
            )
            giver = people.get(t.assigned_by) or (
                (await _employees(db, [managers.get(t.assigned_to)])).get(managers.get(t.assigned_to))
            )
            if giver and giver.id != assignee.id:
                await _push(
                    db, giver,
                    type="task_overdue",
                    title=f"Overdue: {t.title}",
                    body=f"{_name(assignee)} hasn't finished it (due {due}).",
                    data={"task_id": t.id},
                )
            t.escalation_level = 1
        else:
            # Level k (k ≥ 1) → the manager k levels above the assignee,
            # once the task is k × after_days days late.
            if days_late < t.escalation_level * after_days:
                continue
            chain, cur, seen = [], managers.get(t.assigned_to), {t.assigned_to}
            while cur and cur not in seen:
                seen.add(cur)
                chain.append(cur)
                cur = managers.get(cur)
            # Skip whoever already knows: the giver.
            chain = [c for c in chain if c != t.assigned_by]
            idx = t.escalation_level - 1
            if idx >= len(chain):
                continue  # reached the top
            boss = (await _employees(db, [chain[idx]])).get(chain[idx])
            giver = people.get(t.assigned_by)
            await _push(
                db, boss,
                type="task_escalated",
                title=f"Overdue task in your team: {t.title}",
                body=f"{_name(assignee)} · due {due} ({days_late} days late)"
                + (f" · given by {_name(giver)}" if giver else ""),
                data={"task_id": t.id, "employee_id": assignee.id},
            )
            t.escalation_level += 1
        t.last_escalated_at = _now()
        await db.commit()
        sent += 1
    return {"overdue": len(tasks), "escalated": sent}

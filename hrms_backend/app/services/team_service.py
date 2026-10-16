"""My Team — what a manager needs at a glance about everyone below them.

For one day: each person's attendance status, daily-plan (DWP)
submissions and current sales-target progress, plus rolled-up figures
for every sub-team, so a manager sees "Ravi's team · 12 people · 92 %
present · 78 % of target" and can open it to go a level down.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Attendance,
    DwpSubmission,
    Employee,
    Holiday,
    LeaveRequest,
    SalesTarget,
)

LEFT = ("resigned", "terminated", "separated", "inactive")

# Day status shown for each person.
#   present · late · wfh · half_day · on_leave · absent · not_in (not
#   checked in yet today) · off (holiday / Sunday)
PRESENT_LIKE = {"present", "late", "wfh", "half_day"}


def _name(e: Employee) -> str:
    return f"{e.first_name} {e.last_name}".strip()


async def day_status(
    db: AsyncSession, employee_ids: Iterable[int], on: date
) -> dict[int, dict]:
    """employee id → {status, check_in, check_out}."""
    ids = list(employee_ids)
    if not ids:
        return {}
    rows = {
        a.employee_id: a
        for a in (
            await db.execute(
                select(Attendance).where(
                    Attendance.date == on, Attendance.employee_id.in_(ids)
                )
            )
        ).scalars()
    }
    on_leave = set(
        (
            await db.execute(
                select(LeaveRequest.employee_id).where(
                    LeaveRequest.status == "approved",
                    LeaveRequest.from_date <= on,
                    LeaveRequest.to_date >= on,
                    LeaveRequest.employee_id.in_(ids),
                )
            )
        ).scalars()
    )
    holiday = (
        await db.execute(select(Holiday.id).where(Holiday.date == on).limit(1))
    ).first() is not None
    off_day = holiday or on.weekday() == 6
    today = date.today()

    out: dict[int, dict] = {}
    for i in ids:
        a = rows.get(i)
        if a is not None and a.status in ("present", "half_day", "wfh"):
            status = "present" if a.status == "present" else a.status
            if status == "present" and getattr(a, "is_late", False):
                status = "late"
        elif a is not None and a.check_in and a.status not in ("leave", "holiday"):
            status = "present"
        elif i in on_leave or (a is not None and a.status == "leave"):
            status = "on_leave"
        elif (a is not None and a.status == "holiday") or (a is None and off_day):
            status = "off"
        elif on < today or a is not None:
            status = "absent"
        else:
            status = "not_in"
        out[i] = {
            "status": status,
            "check_in": a.check_in if a else None,
            "check_out": a.check_out if a else None,
        }
    return out


async def dwp_status(
    db: AsyncSession, employee_ids: Iterable[int], on: date
) -> dict[int, set[str]]:
    """employee id → the daily-plan types submitted ("morning", "eod")."""
    ids = list(employee_ids)
    out: dict[int, set[str]] = {i: set() for i in ids}
    if not ids:
        return out
    for emp_id, kind in (
        await db.execute(
            select(DwpSubmission.employee_id, DwpSubmission.type).where(
                DwpSubmission.date == on, DwpSubmission.employee_id.in_(ids)
            )
        )
    ).all():
        out.setdefault(emp_id, set()).add(kind)
    return out


async def current_targets(
    db: AsyncSession, employee_ids: Iterable[int], on: date
) -> dict[int, dict]:
    """employee id → the shortest sales target period covering ``on``."""
    ids = list(employee_ids)
    if not ids:
        return {}
    best: dict[int, SalesTarget] = {}
    for t in (
        await db.execute(
            select(SalesTarget).where(
                SalesTarget.employee_id.in_(ids),
                SalesTarget.period_start <= on,
                SalesTarget.period_end >= on,
            )
        )
    ).scalars():
        cur = best.get(t.employee_id)
        span = (t.period_end - t.period_start).days
        if cur is None or span < (cur.period_end - cur.period_start).days:
            best[t.employee_id] = t
    return {
        i: {
            "period_type": t.period_type,
            "period_start": t.period_start,
            "period_end": t.period_end,
            "target_amount": t.target_amount,
            "achieved_amount": t.achieved_amount or Decimal(0),
            "achievement_pct": _pct(t.achieved_amount or 0, t.target_amount),
        }
        for i, t in best.items()
    }


def _pct(part, whole) -> Optional[float]:
    whole = float(whole or 0)
    return round(float(part or 0) / whole * 100, 1) if whole > 0 else None


def rollup(
    ids: Iterable[int],
    status: dict[int, dict],
    dwp: dict[int, set[str]],
    targets: dict[int, dict],
) -> dict:
    """Summary figures for a group of people."""
    ids = list(ids)
    counts = {k: 0 for k in ("present", "late", "wfh", "half_day", "on_leave", "absent", "not_in", "off")}
    for i in ids:
        counts[status.get(i, {}).get("status", "not_in")] += 1
    working = len(ids) - counts["off"] - counts["on_leave"]
    in_office = sum(counts[k] for k in PRESENT_LIKE)
    with_target = [targets[i] for i in ids if i in targets]
    return {
        "size": len(ids),
        **counts,
        "present_total": in_office,
        "attendance_pct": _pct(in_office, working),
        "dwp_morning": sum(1 for i in ids if "morning" in dwp.get(i, ())),
        "dwp_eod": sum(1 for i in ids if "eod" in dwp.get(i, ())),
        "with_target": len(with_target),
        "target_amount": sum((t["target_amount"] for t in with_target), Decimal(0)),
        "achieved_amount": sum((t["achieved_amount"] for t in with_target), Decimal(0)),
        "target_pct": _pct(
            sum(t["achieved_amount"] for t in with_target),
            sum(t["target_amount"] for t in with_target),
        ),
    }


async def overview(
    db: AsyncSession,
    *,
    root: Optional[Employee],
    visible: Optional[set[int]],
    scope: str,
    on: date,
) -> dict:
    """The team below ``root`` (None = the whole company, for HR /
    Admin / Director). ``scope``: "direct" lists the people reporting
    straight to root with their sub-team rolled up; "all" lists everyone
    below root."""
    staff = {
        e.id: e
        for e in (
            await db.execute(select(Employee).where(Employee.status.not_in(LEFT)))
        ).unique().scalars()
    }
    if visible is not None:
        staff = {i: e for i, e in staff.items() if i in visible}
    children: dict[Optional[int], list[int]] = {}
    for e in staff.values():
        parent = e.reporting_to if e.reporting_to in staff else None
        children.setdefault(parent, []).append(e.id)
    for kids in children.values():
        kids.sort(key=lambda i: _name(staff[i]).lower())

    def below(i: Optional[int]) -> list[int]:
        out, stack, seen = [], list(children.get(i, ())), set()
        while stack:
            c = stack.pop()
            if c in seen or c == i:
                continue
            seen.add(c)
            out.append(c)
            stack.extend(children.get(c, ()))
        return out

    if root is not None:
        top = [c for c in children.get(root.id, ())]
        everyone = below(root.id)
    else:
        top = children.get(None, [])
        everyone = list(staff)

    status = await day_status(db, everyone, on)
    dwp = await dwp_status(db, everyone, on)
    targets = await current_targets(db, everyone, on)

    level = {}
    frontier, depth = list(top), 1
    while frontier:
        nxt = []
        for i in frontier:
            if i not in level:
                level[i] = depth
                nxt.extend(children.get(i, ()))
        frontier, depth = nxt, depth + 1

    listed = top if scope == "direct" else sorted(
        everyone, key=lambda i: (level.get(i, 99), _name(staff[i]).lower())
    )
    members = []
    for i in listed:
        e = staff[i]
        sub = below(i)
        manager = staff.get(e.reporting_to)
        members.append(
            {
                "employee_id": e.id,
                "employee_code": e.employee_code,
                "name": _name(e),
                "designation": e.designation.name if e.designation else None,
                "department": e.department.name if e.department else None,
                "photo_url": e.photo_url,
                "reporting_to": e.reporting_to,
                "manager_name": _name(manager) if manager else None,
                "level": level.get(i, 1),
                "direct_reports": len(children.get(i, ())),
                "today": status[i],
                "dwp_morning": "morning" in dwp[i],
                "dwp_eod": "eod" in dwp[i],
                "target": targets.get(i),
                "team": rollup(sub, status, dwp, targets) if sub else None,
            }
        )
    return {
        "root": (
            {
                "employee_id": root.id,
                "name": _name(root),
                "designation": root.designation.name if root.designation else None,
                "reporting_to": root.reporting_to,
            }
            if root
            else None
        ),
        "scope": scope,
        "on_date": on,
        "summary": rollup(everyone, status, dwp, targets),
        "direct_count": len(top),
        "members": members,
    }


async def manager_chain(db: AsyncSession, employee: Employee, stop_at: Optional[int]) -> list[dict]:
    """Managers above ``employee``, nearest first, up to (and including)
    ``stop_at`` — or to the top when None."""
    chain: list[dict] = []
    seen = {employee.id}
    cur = employee.reporting_to
    while cur and cur not in seen:
        seen.add(cur)
        m = (await db.execute(select(Employee).where(Employee.id == cur))).scalar_one_or_none()
        if not m:
            break
        chain.append(
            {
                "employee_id": m.id,
                "name": _name(m),
                "designation": m.designation.name if m.designation else None,
            }
        )
        if cur == stop_at:
            break
        cur = m.reporting_to
    return chain

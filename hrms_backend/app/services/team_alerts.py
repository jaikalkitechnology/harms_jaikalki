"""Team alerts — the nudges that keep managers and their people on track.

- Morning digest (daily, to everyone with a team): who's absent / late /
  not in, who hasn't sent a morning plan, overdue tasks.
- Plan reminder (daily, to employees who usually send a morning plan
  but haven't today).
- Overdue-task escalation (daily) — see task_service.escalate_overdue.
- Weekly summary (to everyone with a team): last week's attendance,
  daily plans, tasks and target progress for each sub-team, and who is
  behind target; people behind target get a nudge too.
- Nightly target refresh.

Times and switches live in SystemConfig ``team_alerts`` (Settings → Team
alerts). Celery beat calls ``run_due`` every 10 minutes; each job runs
once per day (or week) at or after its time.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Attendance,
    DwpSubmission,
    Employee,
    Holiday,
    SystemConfig,
    User,
    WorkTask,
)
from app.services import team_service as team
from app.services.task_service import escalate_overdue, task_counts

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")
KEY = "team_alerts"
STATE_KEY = "team_alerts.state"

DEFAULTS: dict = {
    "morning_digest": True,
    "digest_time": "10:30",
    "plan_reminder": True,
    "plan_reminder_time": "10:00",
    "task_escalation": True,
    "escalate_after_days": 2,
    "weekly_summary": True,
    "weekly_day": 0,  # Monday
    "weekly_time": "09:30",
    "target_alerts": True,
    # Behind = progress more than this many points under time elapsed.
    "target_behind_by": 20,
    # Calculate last period's incentives at the start of a new one.
    "incentive_auto_calc": True,
}
BOOLS = (
    "morning_digest", "plan_reminder", "task_escalation", "weekly_summary",
    "target_alerts", "incentive_auto_calc",
)
TIMES = ("digest_time", "plan_reminder_time", "weekly_time")


# ── Settings ─────────────────────────────────────────────────────────
async def _row(db: AsyncSession, key: str) -> Optional[SystemConfig]:
    return (await db.execute(select(SystemConfig).where(SystemConfig.key == key))).scalar_one_or_none()


async def get_settings(db: AsyncSession) -> dict:
    row = await _row(db, KEY)
    stored = row.value if row and isinstance(row.value, dict) else {}
    return {**DEFAULTS, **{k: v for k, v in stored.items() if k in DEFAULTS}}


def _valid_time(v: str) -> bool:
    try:
        h, m = (int(x) for x in v.split(":"))
        return 0 <= h < 24 and 0 <= m < 60
    except Exception:
        return False


async def set_settings(db: AsyncSession, changes: dict, actor: Optional[User] = None) -> dict:
    clean: dict = {}
    for k, v in changes.items():
        if v is None or k not in DEFAULTS:
            continue
        if k in BOOLS:
            clean[k] = bool(v)
        elif k in TIMES:
            if not _valid_time(str(v)):
                raise ValueError(f"{k} must be HH:MM")
            clean[k] = str(v)
        elif k == "weekly_day":
            clean[k] = int(v) % 7
        elif k in ("escalate_after_days", "target_behind_by"):
            clean[k] = max(1, min(int(v), 60))
    row = await _row(db, KEY)
    merged = {**(row.value if row and isinstance(row.value, dict) else {}), **clean}
    if row:
        row.value = merged
        row.updated_by = actor.id if actor else row.updated_by
    else:
        db.add(SystemConfig(key=KEY, value=merged, category="alerts",
                            description="Team alert switches and times",
                            updated_by=actor.id if actor else None))
    await db.commit()
    return await get_settings(db)


# ── Helpers ──────────────────────────────────────────────────────────
def _name(e: Employee) -> str:
    return f"{e.first_name} {e.last_name}".strip()


def _first(e: Employee) -> str:
    return e.first_name or _name(e)


def _names(people: list[Employee], cap: int = 3) -> str:
    shown = ", ".join(_first(p) for p in people[:cap])
    return shown + (f" +{len(people) - cap}" if len(people) > cap else "")


async def _org(db: AsyncSession) -> tuple[dict[int, Employee], dict[int, list[int]]]:
    """Current staff and manager → direct reports."""
    staff = {
        e.id: e
        for e in (
            await db.execute(select(Employee).where(Employee.status.not_in(team.LEFT)))
        ).unique().scalars()
    }
    kids: dict[int, list[int]] = {}
    for e in staff.values():
        if e.reporting_to in staff and e.reporting_to != e.id:
            kids.setdefault(e.reporting_to, []).append(e.id)
    return staff, kids


def _below(kids: dict[int, list[int]], root: int) -> list[int]:
    out, stack, seen = [], list(kids.get(root, ())), {root}
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
        stack.extend(kids.get(c, ()))
    return out


async def _send(db: AsyncSession, emp: Employee, *, type: str, title: str, body: str, data: dict) -> bool:
    if not emp.user_id:
        return False
    from app.services.notification_service import notify

    try:
        await notify(db, user_id=emp.user_id, type=type, title=title, body=body,
                     data=data, send_push=True)
        return True
    except Exception:  # pragma: no cover
        log.exception("alert to %s failed", emp.id)
        await db.rollback()
        return False


# ── Morning digest ───────────────────────────────────────────────────
def digest_for(
    manager: Employee,
    staff: dict[int, Employee],
    kids: dict[int, list[int]],
    status: dict[int, dict],
    dwp: dict[int, set[str]],
    tasks: dict[int, dict],
) -> Optional[dict]:
    direct = [staff[i] for i in kids.get(manager.id, ())]
    everyone = [staff[i] for i in _below(kids, manager.id)]
    if not everyone:
        return None
    st = lambda e: status[e.id]["status"]  # noqa: E731
    working = [e for e in everyone if st(e) not in ("off", "on_leave")]
    if not working:
        return None  # holiday / everyone away
    absent = [e for e in direct if st(e) == "absent"]
    not_in = [e for e in direct if st(e) == "not_in"]
    late = [e for e in direct if st(e) == "late"]
    no_plan = [e for e in direct if st(e) not in ("off", "on_leave") and "morning" not in dwp[e.id]]
    overdue = sum(tasks[e.id]["overdue"] for e in everyone)
    present = sum(1 for e in everyone if st(e) in team.PRESENT_LIKE)

    parts = []
    if absent:
        parts.append(f"{len(absent)} absent ({_names(absent)})")
    if not_in:
        parts.append(f"{len(not_in)} not in yet ({_names(not_in)})")
    if late:
        parts.append(f"{len(late)} late ({_names(late)})")
    if no_plan:
        parts.append(f"{len(no_plan)} without a morning plan")
    if overdue:
        parts.append(f"{overdue} overdue task{'s' if overdue != 1 else ''}")
    # Names are for direct reports; the head-count and overdue tasks
    # cover everyone below.
    lead = "Direct reports: " if len(everyone) > len(direct) and parts else ""
    return {
        "title": f"Team today: {present}/{len(working)} in",
        "body": lead + ("; ".join(parts) + "." if parts else "Everyone is on track."),
        "data": {"route": "/team"},
    }


async def morning_digest(db: AsyncSession, on: Optional[date] = None, *, only: Optional[int] = None, send: bool = True) -> dict:
    on = on or datetime.now(IST).date()
    staff, kids = await _org(db)
    managers = [staff[m] for m in kids if m in staff and (only is None or m == only)]
    if not managers:
        return {"managers": 0, "sent": 0, "messages": []}
    ids = list(staff)
    status = await team.day_status(db, ids, on)
    dwp = await team.dwp_status(db, ids, on)
    tasks = await task_counts(db, ids)
    sent, messages = 0, []
    for m in managers:
        msg = digest_for(m, staff, kids, status, dwp, tasks)
        if not msg:
            continue
        messages.append({"employee_id": m.id, **msg})
        if send and await _send(db, m, type="team_digest", **msg):
            sent += 1
    return {"managers": len(managers), "sent": sent, "messages": messages}


# ── Plan reminder ────────────────────────────────────────────────────
async def plan_reminder(db: AsyncSession, on: Optional[date] = None) -> dict:
    """Nudge people who sent a morning plan in the last two weeks but
    not today (so departments that don't use daily plans aren't
    bothered)."""
    on = on or datetime.now(IST).date()
    regular = set(
        (
            await db.execute(
                select(DwpSubmission.employee_id)
                .where(DwpSubmission.type == "morning")
                .where(DwpSubmission.date >= on - timedelta(days=14), DwpSubmission.date < on)
                .distinct()
            )
        ).scalars()
    )
    staff, _ = await _org(db)
    ids = [i for i in regular if i in staff]
    status = await team.day_status(db, ids, on)
    dwp = await team.dwp_status(db, ids, on)
    sent = 0
    for i in ids:
        if status[i]["status"] in ("off", "on_leave") or "morning" in dwp[i]:
            continue
        if await _send(
            db, staff[i], type="plan_reminder",
            title="Morning plan pending",
            body="Share today's plan so your manager knows what you're on.",
            data={"route": "/dwp"},
        ):
            sent += 1
    return {"reminded": sent}


# ── Weekly summary + behind-target ───────────────────────────────────
async def _working_days(db: AsyncSession, start: date, end: date) -> int:
    holidays = set(
        (await db.execute(select(Holiday.date).where(Holiday.date >= start, Holiday.date <= end))).scalars()
    )
    n, d = 0, start
    while d <= end:
        if d.weekday() != 6 and d not in holidays:
            n += 1
        d += timedelta(days=1)
    return max(n, 1)


async def _week_stats(db: AsyncSession, ids: list[int], start: date, end: date) -> dict[int, dict]:
    out = {i: {"present": 0, "plans": 0, "done": 0} for i in ids}
    if not ids:
        return out
    for emp_id, n in (
        await db.execute(
            select(Attendance.employee_id, func.count())
            .where(Attendance.employee_id.in_(ids), Attendance.date >= start, Attendance.date <= end)
            .where(Attendance.status.in_(("present", "half_day", "wfh")))
            .group_by(Attendance.employee_id)
        )
    ).all():
        out[emp_id]["present"] = n
    for emp_id, n in (
        await db.execute(
            select(DwpSubmission.employee_id, func.count())
            .where(DwpSubmission.employee_id.in_(ids), DwpSubmission.type == "morning")
            .where(DwpSubmission.date >= start, DwpSubmission.date <= end)
            .group_by(DwpSubmission.employee_id)
        )
    ).all():
        out[emp_id]["plans"] = n
    s_dt, e_dt = datetime.combine(start, time.min), datetime.combine(end, time.max)
    for emp_id, n in (
        await db.execute(
            select(WorkTask.assigned_to, func.count())
            .where(WorkTask.assigned_to.in_(ids), WorkTask.status == "done")
            .where(WorkTask.completed_at >= s_dt, WorkTask.completed_at <= e_dt)
            .group_by(WorkTask.assigned_to)
        )
    ).all():
        out[emp_id]["done"] = n
    return out


def _pace(t: dict, on: date) -> tuple[float, float]:
    """(progress %, share of the period gone %)."""
    span = (t["period_end"] - t["period_start"]).days + 1
    gone = min(max((on - t["period_start"]).days + 1, 0), span)
    return float(t["achievement_pct"] or 0), round(gone / span * 100, 1)


async def behind_target(db: AsyncSession, ids: list[int], on: date, behind_by: int) -> dict[int, dict]:
    """People whose main target is well behind the calendar."""
    out = {}
    for i, t in (await team.current_targets(db, ids, on)).items():
        pct, gone = _pace(t, on)
        if gone >= 30 and pct < gone - behind_by:
            out[i] = {**t, "pct": pct, "gone": gone}
    return out


async def weekly_summary(db: AsyncSession, on: Optional[date] = None, *, only: Optional[int] = None, send: bool = True, nudge: bool = True) -> dict:
    on = on or datetime.now(IST).date()
    end = on - timedelta(days=1)
    start = end - timedelta(days=6)
    days = await _working_days(db, start, end)
    cfg = await get_settings(db)
    staff, kids = await _org(db)
    ids = list(staff)
    week = await _week_stats(db, ids, start, end)
    tasks = await task_counts(db, ids)
    targets = await team.current_targets(db, ids, on)
    behind = (
        await behind_target(db, ids, on, int(cfg["target_behind_by"]))
        if cfg["target_alerts"]
        else {}
    )

    def line(label: str, group: list[int]) -> str:
        n = len(group) or 1
        att = round(sum(week[i]["present"] for i in group) / (n * days) * 100)
        plans = round(sum(week[i]["plans"] for i in group) / (n * days) * 100)
        done = sum(week[i]["done"] for i in group)
        overdue = sum(tasks[i]["overdue"] for i in group)
        r = team.rollup(group, {i: {"status": "off"} for i in group}, {}, targets)
        bits = [f"{att}% attendance", f"{plans}% daily plans", f"{done} tasks done"]
        if overdue:
            bits.append(f"{overdue} overdue")
        if r["target_pct"] is not None:
            bits.append(f"{r['target_pct']:.0f}% of target")
        return f"{label}: " + ", ".join(bits)

    sent, messages = 0, []
    for m_id, direct in kids.items():
        if m_id not in staff or (only is not None and m_id != only):
            continue
        m = staff[m_id]
        everyone = _below(kids, m_id)
        lines = [line("Your team", everyone)]
        for d in direct:
            sub = _below(kids, d)
            if sub:
                lines.append(line(f"{_first(staff[d])}'s team", [d, *sub]))
        lagging = [staff[i] for i in everyone if i in behind]
        if lagging:
            lines.append(
                "Behind target: "
                + ", ".join(f"{_first(e)} {behind[e.id]['pct']:.0f}%" for e in lagging[:5])
                + (f" +{len(lagging) - 5}" if len(lagging) > 5 else "")
            )
        msg = {
            "title": f"Last week ({start.strftime('%d %b')} – {end.strftime('%d %b')})",
            "body": "\n".join(lines),
            "data": {"route": "/team"},
        }
        messages.append({"employee_id": m_id, **msg})
        if send and await _send(db, m, type="team_weekly", **msg):
            sent += 1

    nudged = 0
    if send and nudge:
        for i, t in behind.items():
            unit = "" if t["metric"] == "sales_amount" else f" ({t['metric'].replace('_', ' ')})"
            if await _send(
                db, staff[i], type="target_behind",
                title="Your target needs attention",
                body=f"You're at {t['pct']:.0f}% of your {t['period_type']} target{unit} "
                     f"with {t['gone']:.0f}% of the period gone.",
                data={"route": "/sales/targets"},
            ):
                nudged += 1
    return {"managers": len(messages), "sent": sent, "behind": len(behind), "nudged": nudged, "messages": messages}


# ── Dispatcher ───────────────────────────────────────────────────────
JOBS = (
    "plan_reminder", "morning_digest", "task_escalation", "weekly_summary",
    "target_refresh", "incentive_calc",
)


async def run_job(db: AsyncSession, job: str) -> dict:
    cfg = await get_settings(db)
    if job == "morning_digest":
        return await morning_digest(db)
    if job == "plan_reminder":
        return await plan_reminder(db)
    if job == "task_escalation":
        return await escalate_overdue(db, after_days=int(cfg["escalate_after_days"]))
    if job == "weekly_summary":
        return await weekly_summary(db)
    if job == "target_refresh":
        from app.services.sales_service import refresh_all_current_targets

        return {"refreshed": await refresh_all_current_targets(db)}
    if job == "incentive_calc":
        from app.services.incentive_service import auto_calculate

        return await auto_calculate(db)
    raise ValueError(f"Unknown job {job}")


def _due_today(now: datetime, at: str) -> bool:
    h, m = (int(x) for x in at.split(":"))
    return (now.hour, now.minute) >= (h, m)


async def run_due(db: AsyncSession, now: Optional[datetime] = None) -> dict:
    """Run every job whose time has come and that hasn't run yet today
    (this week, for the weekly one). Safe to call as often as you like."""
    now = now or datetime.now(IST)
    today = now.date().isoformat()
    cfg = await get_settings(db)
    row = await _row(db, STATE_KEY)
    state = dict(row.value) if row and isinstance(row.value, dict) else {}
    week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]}"

    plan = {
        "plan_reminder": cfg["plan_reminder"] and _due_today(now, cfg["plan_reminder_time"]),
        "morning_digest": cfg["morning_digest"] and _due_today(now, cfg["digest_time"]),
        "task_escalation": cfg["task_escalation"] and _due_today(now, cfg["digest_time"]),
        "target_refresh": now.hour >= 2,
        # After the nightly target refresh, so last period is final.
        "incentive_calc": cfg["incentive_auto_calc"] and now.hour >= 6,
        "weekly_summary": cfg["weekly_summary"]
        and now.weekday() == int(cfg["weekly_day"])
        and _due_today(now, cfg["weekly_time"]),
    }
    ran: dict = {}
    for job, due in plan.items():
        stamp = week if job == "weekly_summary" else today
        if not due or state.get(job) == stamp:
            continue
        # Claim first so an overlapping run doesn't send twice.
        state[job] = stamp
        await _save_state(db, row, state)
        row = await _row(db, STATE_KEY)
        try:
            result = await run_job(db, job)
            ran[job] = {k: v for k, v in result.items() if k != "messages"}
        except Exception as exc:  # pragma: no cover
            log.exception("team alert job %s failed", job)
            ran[job] = {"error": str(exc)}
    return ran


async def _save_state(db: AsyncSession, row: Optional[SystemConfig], state: dict) -> None:
    if row:
        row.value = dict(state)
    else:
        db.add(SystemConfig(key=STATE_KEY, value=dict(state), category="alerts",
                            description="When each team alert last ran"))
    await db.commit()

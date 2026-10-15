"""Company-asset return as part of exit clearance (the assets NOC).

An exiting employee must hand back every asset still assigned to them.
This module answers "what's still out?", keeps the resignation's
``assets_returned`` checklist item in step with the asset register, and
tells the employee and their reporting manager as items come back.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, AssetAssignment, AssetCategory, Employee, Resignation

log = logging.getLogger(__name__)

# Exits that are under way (asset return is due or upcoming).
OPEN_EXIT_STATES = (
    "manager_review", "accepted", "in_notice", "ndc_pending", "cleared",
)
# States in which the NDC checklist is live.
NDC_STATES = ("in_notice", "ndc_pending", "cleared")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def held_assets(db: AsyncSession, employee_id: int) -> Sequence[Asset]:
    return (
        await db.execute(
            select(Asset)
            .where(Asset.assigned_to == employee_id)
            .where(Asset.status == "assigned")
            .order_by(Asset.parent_asset_id.is_not(None), Asset.asset_tag)
        )
    ).scalars().all()


async def held_counts(
    db: AsyncSession, employee_ids: Iterable[int]
) -> dict[int, int]:
    ids = list(set(employee_ids))
    if not ids:
        return {}
    rows = (
        await db.execute(
            select(Asset.assigned_to, func.count())
            .where(Asset.assigned_to.in_(ids))
            .where(Asset.status == "assigned")
            .group_by(Asset.assigned_to)
        )
    ).all()
    return {emp_id: n for emp_id, n in rows}


async def open_exit(db: AsyncSession, employee_id: int) -> Optional[Resignation]:
    return (
        await db.execute(
            select(Resignation)
            .where(Resignation.employee_id == employee_id)
            .where(Resignation.status.in_(OPEN_EXIT_STATES))
            .order_by(Resignation.requested_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _category_names(db: AsyncSession) -> dict[str, str]:
    return {
        c.code: c.name
        for c in (await db.execute(select(AssetCategory))).scalars().all()
    }


def _asset_row(a: Asset, names: dict[str, str]) -> dict:
    return {
        "id": a.id,
        "asset_tag": a.asset_tag,
        "name": a.name,
        "category": a.category,
        "category_name": names.get(a.category, a.category.replace("_", " ").title()),
        "brand": a.brand,
        "model": a.model,
        "serial_number": a.serial_number,
        "condition": a.condition,
        "parent_asset_id": a.parent_asset_id,
        "assigned_at": a.assigned_at,
    }


async def clearance(
    db: AsyncSession, employee_id: int, *, since: Optional[datetime] = None
) -> dict:
    """Assets still with the employee, and those handed back since
    ``since`` (the resignation date) — the asset NOC status."""
    names = await _category_names(db)
    pending = [_asset_row(a, names) for a in await held_assets(db, employee_id)]

    returned: list[dict] = []
    if since is not None:
        rows = (
            await db.execute(
                select(AssetAssignment, Asset)
                .join(Asset, Asset.id == AssetAssignment.asset_id)
                .where(AssetAssignment.employee_id == employee_id)
                .where(AssetAssignment.returned_at.is_not(None))
                .where(AssetAssignment.returned_at >= since)
                .order_by(AssetAssignment.returned_at.desc())
            )
        ).all()
        for assignment, asset in rows:
            row = _asset_row(asset, names)
            row["returned_at"] = assignment.returned_at
            row["return_condition"] = assignment.return_condition
            returned.append(row)

    return {
        "employee_id": employee_id,
        "cleared": not pending,
        "pending_count": len(pending),
        "returned_count": len(returned),
        "pending": pending,
        "returned": returned,
    }


async def sync_ndc(db: AsyncSession, employee_id: int) -> Optional[Resignation]:
    """Mirror the asset register into the exit checklist's
    ``assets_returned`` item, moving the exit along like a manual tick."""
    from app.services.resignation_service import DEFAULT_NDC

    res = (
        await db.execute(
            select(Resignation)
            .where(Resignation.employee_id == employee_id)
            .where(Resignation.status.in_(NDC_STATES))
            .order_by(Resignation.requested_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if res is None:
        return None
    done = not await held_assets(db, employee_id)
    checklist = dict(res.ndc_checklist or DEFAULT_NDC)
    if checklist.get("assets_returned") == done:
        return res
    checklist["assets_returned"] = done
    res.ndc_checklist = checklist
    if res.status in ("in_notice", "ndc_pending"):
        if all(checklist.values()):
            res.status = "cleared"
            res.hr_cleared_at = _now()
        elif res.status == "in_notice":
            res.status = "ndc_pending"
    await db.commit()
    await db.refresh(res)
    return res


async def _recipients(db: AsyncSession, employee: Employee) -> list[int]:
    """User ids of the employee and their reporting manager."""
    ids = [employee.user_id] if employee.user_id else []
    if employee.reporting_to:
        manager = (
            await db.execute(select(Employee).where(Employee.id == employee.reporting_to))
        ).scalar_one_or_none()
        if manager and manager.user_id:
            ids.append(manager.user_id)
    return ids


async def _notify(
    db: AsyncSession, employee: Employee, *, type: str, title: str, body: str,
    data: dict,
) -> None:
    from app.services.notification_service import notify

    for user_id in await _recipients(db, employee):
        try:
            await notify(
                db, user_id=user_id, type=type, title=title, body=body,
                data=data, send_push=True,
            )
        except Exception:  # pragma: no cover - best effort
            log.exception("asset clearance notification failed")


async def on_assets_changed(
    db: AsyncSession, employee_id: int, *, returned: Sequence[Asset] = ()
) -> None:
    """After assets come back: update the checklist and, during an exit,
    tell the employee and their manager what's left."""
    try:
        await sync_ndc(db, employee_id)
        res = await open_exit(db, employee_id)
        if res is None or not returned:
            return
        employee = (
            await db.execute(select(Employee).where(Employee.id == employee_id))
        ).scalar_one_or_none()
        if employee is None:
            return
        left = len(await held_assets(db, employee_id))
        what = ", ".join(f"{a.name} ({a.asset_tag})" for a in returned)
        name = f"{employee.first_name} {employee.last_name}".strip()
        if left:
            title = f"Asset returned · {left} still to return"
            body = f"{name} returned {what}. {left} company asset(s) still to return."
        else:
            title = "All company assets returned"
            body = f"{name} returned {what}. Asset clearance is complete."
        await _notify(
            db, employee, type="asset_return", title=title, body=body,
            data={"resignation_id": res.id, "employee_id": employee_id,
                  "pending": left},
        )
    except Exception:  # never let a notification break the return itself
        log.exception("asset clearance update failed")


async def on_exit_started(db: AsyncSession, res: Resignation) -> None:
    """Exit accepted / created: set the checklist item and list what has
    to come back before the last working day."""
    try:
        await sync_ndc(db, res.employee_id)
        employee = (
            await db.execute(select(Employee).where(Employee.id == res.employee_id))
        ).scalar_one_or_none()
        held = await held_assets(db, res.employee_id)
        if employee is None or not held:
            return
        lwd = res.actual_last_working_day or res.proposed_last_working_day
        items = ", ".join(f"{a.name} ({a.asset_tag})" for a in held)
        name = f"{employee.first_name} {employee.last_name}".strip()
        await _notify(
            db, employee, type="asset_return_due",
            title=f"{len(held)} company asset(s) to return",
            body=(
                f"{name}: please hand back {items} before the last working "
                f"day ({lwd.strftime('%d %b %Y')}) for exit clearance."
            ),
            data={"resignation_id": res.id, "employee_id": res.employee_id,
                  "pending": len(held)},
        )
    except Exception:
        log.exception("asset clearance start failed")

"""Sales service: leads, quotes, orders, targets, promotions."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    Customer,
    Employee,
    Lead,
    Opportunity,
    Product,
    PromotionActivity,
    Quote,
    SalesOrder,
    SalesTarget,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _money(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Lead stage → score mapping (used by auto-scoring)
_STAGE_SCORE = {
    "new": 10,
    "contacted": 25,
    "qualified": 50,
    "proposal": 70,
    "negotiation": 85,
    "won": 100,
    "lost": 0,
}


# ── Lead service ──────────────────────────────────────────────────────
async def create_lead(
    db: AsyncSession,
    *,
    payload: dict,
) -> Lead:
    if payload.get("customer_id"):
        cust = (
            await db.execute(
                select(Customer).where(Customer.id == payload["customer_id"])
            )
        ).scalar_one_or_none()
        if not cust:
            raise NotFoundError("Customer not found")
    lead = Lead(
        **payload,
        stage="new",
        score=_STAGE_SCORE["new"],
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


async def list_leads(
    db: AsyncSession,
    *,
    assigned_to: Optional[int] = None,
    stage: Optional[str] = None,
    source: Optional[str] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    won_status: Optional[str] = None,
    assigned_in: Optional[set[int]] = None,
    include_unassigned: bool = False,
    limit: int = 500,
) -> Sequence[Lead]:
    """``assigned_in`` limits to leads owned by those employees (the
    caller's team); None = no limit."""
    from sqlalchemy import or_

    stmt = select(Lead)
    if assigned_in is not None:
        owned = Lead.assigned_to.in_(assigned_in or {-1})
        stmt = stmt.where(
            or_(owned, Lead.assigned_to.is_(None)) if include_unassigned else owned
        )
    if assigned_to is not None:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
    if stage:
        stmt = stmt.where(Lead.stage == stage)
    if source:
        stmt = stmt.where(Lead.source == source)
    if customer_id is not None:
        stmt = stmt.where(Lead.customer_id == customer_id)
    if won_status in {"pending", "approved", "rejected"}:
        stmt = stmt.where(Lead.won_approval_status == won_status)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Lead.contact_name.ilike(like),
                Lead.contact_email.ilike(like),
                Lead.contact_phone.ilike(like),
                Lead.notes.ilike(like),
            )
        )
    stmt = stmt.order_by(Lead.created_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


async def update_lead(
    db: AsyncSession, lead_id: int, *, payload: dict, actor=None,
) -> Lead:
    from app.models import LeadActivity

    lead = await get_lead(db, lead_id)
    prev_assignee = lead.assigned_to
    allowed = {
        "customer_id", "contact_name", "contact_phone", "contact_email",
        "source", "expected_value", "expected_close_date",
        "assigned_to", "next_action", "next_action_date",
        "notes", "lost_reason",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(lead, k, v)
    # Auto-log assignment changes for the activity timeline.
    if "assigned_to" in payload and prev_assignee != lead.assigned_to:
        db.add(
            LeadActivity(
                lead_id=lead.id,
                actor_user_id=actor.id if actor else None,
                actor_label=getattr(actor, "full_name", None) if actor else None,
                activity_type="assignment",
                body=f"Assigned to employee #{lead.assigned_to}"
                if lead.assigned_to else "Unassigned",
            )
        )
    await db.commit()
    await db.refresh(lead)
    return lead


async def delete_lead(db: AsyncSession, lead_id: int) -> None:
    lead = await get_lead(db, lead_id)
    await db.delete(lead)
    await db.commit()


# ── Lead activity (timeline) ──────────────────────────────────────────
async def list_lead_activities(db: AsyncSession, lead_id: int):
    from app.models import LeadActivity

    rows = (
        await db.execute(
            select(LeadActivity)
            .where(LeadActivity.lead_id == lead_id)
            .order_by(LeadActivity.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def add_lead_comment(
    db: AsyncSession, lead_id: int, *, body: str, actor,
):
    from app.models import LeadActivity

    await get_lead(db, lead_id)  # 404 if missing
    row = LeadActivity(
        lead_id=lead_id,
        actor_user_id=actor.id,
        actor_label=getattr(actor, "full_name", None),
        activity_type="comment",
        body=body,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_lead(db: AsyncSession, lead_id: int) -> Lead:
    lead = (
        await db.execute(select(Lead).where(Lead.id == lead_id))
    ).scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead not found")
    return lead


def _actor_can_approve(actor) -> bool:
    if actor is None:
        return False
    perms = getattr(actor, "permission_codes", None) or set()
    return "approval.act" in perms or "system.config" in perms


async def update_lead_stage(
    db: AsyncSession,
    lead_id: int,
    *,
    stage: str,
    lost_reason: Optional[str] = None,
    actor=None,
) -> Lead:
    from app.models import LeadActivity

    lead = await get_lead(db, lead_id)
    if lead.stage == stage and stage != "won":
        return lead
    if stage == "lost" and not lost_reason:
        raise ValidationError("lost_reason is required when marking a lead as lost")
    prev = lead.stage
    lead.stage = stage
    lead.score = _STAGE_SCORE.get(stage, lead.score)
    if stage == "lost":
        lead.lost_reason = lost_reason

    # Won-approval workflow.
    if stage == "won":
        if _actor_can_approve(actor):
            # Admin direct close → auto-approve.
            lead.won_approval_status = "approved"
            lead.won_requested_at = lead.won_requested_at or _now()
            lead.won_decided_at = _now()
            lead.won_decided_by_user_id = getattr(actor, "id", None)
            lead.won_rejection_reason = None
            activity_body = "Closed-won (admin direct)"
        else:
            # Sales rep request → goes to pending queue.
            lead.won_approval_status = "pending"
            lead.won_requested_at = _now()
            lead.won_decided_at = None
            lead.won_decided_by_user_id = None
            lead.won_rejection_reason = None
            activity_body = "Won submitted — awaiting admin approval"
    else:
        # Leaving the won state clears any prior decision so that a
        # later re-promotion goes through the queue cleanly.
        if prev == "won":
            lead.won_approval_status = None
            lead.won_decided_at = None
            lead.won_decided_by_user_id = None
        activity_body = lost_reason if stage == "lost" else None

    db.add(
        LeadActivity(
            lead_id=lead.id,
            actor_user_id=actor.id if actor else None,
            actor_label=getattr(actor, "full_name", None) if actor else None,
            activity_type="stage_change",
            from_stage=prev,
            to_stage=stage,
            body=activity_body,
        )
    )
    await db.commit()
    await db.refresh(lead)
    return lead


async def decide_won(
    db: AsyncSession,
    lead_id: int,
    *,
    decision: str,
    reason: Optional[str] = None,
    actor,
) -> Lead:
    """Admin approves or rejects a pending won lead.

    Approve: keeps stage="won" and flips status to "approved".
    Reject: stage rolls back to "negotiation" and stores the reason."""
    from app.models import LeadActivity

    if decision not in {"approve", "reject"}:
        raise ValidationError("decision must be approve or reject")

    lead = await get_lead(db, lead_id)
    if lead.won_approval_status != "pending" or lead.stage != "won":
        raise ValidationError("Lead has no pending won-approval to act on")

    now = _now()
    if decision == "approve":
        lead.won_approval_status = "approved"
        lead.won_decided_at = now
        lead.won_decided_by_user_id = getattr(actor, "id", None)
        lead.won_rejection_reason = None
        db.add(
            LeadActivity(
                lead_id=lead.id,
                actor_user_id=actor.id,
                actor_label=getattr(actor, "full_name", None),
                activity_type="system",
                body="Won approved by admin",
            )
        )
    else:
        prev_stage = lead.stage
        lead.won_approval_status = "rejected"
        lead.won_rejection_reason = (reason or "").strip() or None
        lead.won_decided_at = now
        lead.won_decided_by_user_id = getattr(actor, "id", None)
        # Roll the lead back so the rep can keep working it.
        lead.stage = "negotiation"
        lead.score = _STAGE_SCORE["negotiation"]
        db.add(
            LeadActivity(
                lead_id=lead.id,
                actor_user_id=actor.id,
                actor_label=getattr(actor, "full_name", None),
                activity_type="stage_change",
                from_stage=prev_stage,
                to_stage="negotiation",
                body=f"Won rejected by admin: {lead.won_rejection_reason or 'no reason given'}",
            )
        )
    await db.commit()
    await db.refresh(lead)
    return lead


async def list_pending_won_leads(db: AsyncSession) -> Sequence[Lead]:
    return (
        await db.execute(
            select(Lead)
            .where(Lead.stage == "won")
            .where(Lead.won_approval_status == "pending")
            .order_by(Lead.won_requested_at.desc().nullslast())
        )
    ).scalars().all()


async def pipeline_kanban(
    db: AsyncSession,
    *,
    assigned_to: Optional[int] = None,
    assigned_in: Optional[set[int]] = None,
    include_unassigned: bool = False,
) -> list[dict]:
    stages = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]
    leads = await list_leads(
        db,
        assigned_to=assigned_to,
        assigned_in=assigned_in,
        include_unassigned=include_unassigned,
        limit=500,
    )
    by_stage: dict[str, list[Lead]] = {s: [] for s in stages}
    for ld in leads:
        by_stage.setdefault(ld.stage, []).append(ld)
    return [
        {
            "stage": s,
            "leads": by_stage[s],
            "total_value": sum(
                (ld.expected_value for ld in by_stage[s]), Decimal("0")
            ),
            "count": len(by_stage[s]),
        }
        for s in stages
    ]


# ── Product service ──────────────────────────────────────────────────
async def create_product(db: AsyncSession, *, payload: dict) -> Product:
    existing = (
        await db.execute(select(Product).where(Product.sku == payload["sku"]))
    ).scalar_one_or_none()
    if existing:
        raise ConflictError(f"SKU {payload['sku']} already exists")
    p = Product(**payload, is_active=True)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def list_products(
    db: AsyncSession, *, active_only: bool = True
) -> Sequence[Product]:
    stmt = select(Product)
    if active_only:
        stmt = stmt.where(Product.is_active.is_(True))
    stmt = stmt.order_by(Product.name.asc())
    return (await db.execute(stmt)).scalars().all()


# ── Quote computation helpers ────────────────────────────────────────
def _compute_quote_totals(
    line_items: list[dict], discount_pct: Decimal
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    subtotal = Decimal("0")
    tax = Decimal("0")
    for item in line_items:
        line = Decimal(str(item["unit_price"])) * int(item["quantity"])
        subtotal += line
        tax += line * Decimal(str(item.get("tax_pct", 18))) / Decimal("100")
    subtotal = _money(subtotal)
    discount_amount = _money(subtotal * discount_pct / Decimal("100"))
    tax = _money(tax * (Decimal("1") - discount_pct / Decimal("100")))
    total = _money(subtotal - discount_amount + tax)
    return subtotal, discount_amount, tax, total


async def _next_quote_number(db: AsyncSession) -> str:
    year = _now().year
    prefix = f"JKT/Q/{year}/"
    last = (
        await db.execute(
            select(Quote.quote_number)
            .where(Quote.quote_number.like(f"{prefix}%"))
            .order_by(Quote.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    seq = 1
    if last:
        try:
            seq = int(last.split("/")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


async def create_quote(
    db: AsyncSession,
    *,
    employee: Employee,
    payload: dict,
) -> Quote:
    cust = (
        await db.execute(
            select(Customer).where(Customer.id == payload["customer_id"])
        )
    ).scalar_one_or_none()
    if not cust:
        raise NotFoundError("Customer not found")

    line_items = [
        item.model_dump() if hasattr(item, "model_dump") else dict(item)
        for item in payload["line_items"]
    ]
    if not line_items:
        raise ValidationError("Quote must have at least one line item")
    # Normalise Decimals → str for JSON.
    for li in line_items:
        li["unit_price"] = str(li["unit_price"])
        li["tax_pct"] = str(li.get("tax_pct", "18"))

    discount_pct = Decimal(str(payload.get("discount_pct", "0")))
    subtotal, discount_amount, tax, total = _compute_quote_totals(
        line_items, discount_pct
    )

    quote = Quote(
        quote_number=await _next_quote_number(db),
        customer_id=cust.id,
        employee_id=employee.id,
        lead_id=payload.get("lead_id"),
        line_items=line_items,
        subtotal=subtotal,
        discount_pct=discount_pct,
        discount_amount=discount_amount,
        tax_amount=tax,
        total_amount=total,
        valid_until=payload.get("valid_until"),
        status="draft",
        notes=payload.get("notes"),
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return quote


async def list_quotes(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Sequence[Quote]:
    stmt = select(Quote)
    if employee_id is not None:
        stmt = stmt.where(Quote.employee_id == employee_id)
    if customer_id is not None:
        stmt = stmt.where(Quote.customer_id == customer_id)
    if status:
        stmt = stmt.where(Quote.status == status)
    stmt = stmt.order_by(Quote.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def get_quote(db: AsyncSession, quote_id: int) -> Quote:
    q = (
        await db.execute(select(Quote).where(Quote.id == quote_id))
    ).scalar_one_or_none()
    if not q:
        raise NotFoundError("Quote not found")
    return q


async def update_quote_status(
    db: AsyncSession,
    quote_id: int,
    *,
    status: str,
    signature_url: Optional[str] = None,
) -> Quote:
    q = await get_quote(db, quote_id)
    q.status = status
    if signature_url:
        q.signature_url = signature_url
    await db.commit()
    await db.refresh(q)
    return q


# ── Orders ───────────────────────────────────────────────────────────
async def _next_order_number(db: AsyncSession) -> str:
    year = _now().year
    prefix = f"JKT/SO/{year}/"
    last = (
        await db.execute(
            select(SalesOrder.order_number)
            .where(SalesOrder.order_number.like(f"{prefix}%"))
            .order_by(SalesOrder.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    seq = 1
    if last:
        try:
            seq = int(last.split("/")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


async def create_order(
    db: AsyncSession,
    *,
    employee: Employee,
    payload: dict,
) -> SalesOrder:
    cust = (
        await db.execute(
            select(Customer).where(Customer.id == payload["customer_id"])
        )
    ).scalar_one_or_none()
    if not cust:
        raise NotFoundError("Customer not found")

    line_items = [
        item.model_dump() if hasattr(item, "model_dump") else dict(item)
        for item in payload["line_items"]
    ]
    if not line_items:
        raise ValidationError("Order must have at least one line item")
    for li in line_items:
        li["unit_price"] = str(li["unit_price"])
        li["tax_pct"] = str(li.get("tax_pct", "18"))

    subtotal = _money(
        sum(
            Decimal(str(li["unit_price"])) * int(li["quantity"])
            for li in line_items
        )
    )
    tax = _money(
        sum(
            Decimal(str(li["unit_price"]))
            * int(li["quantity"])
            * Decimal(str(li.get("tax_pct", "18")))
            / Decimal("100")
            for li in line_items
        )
    )
    discount_amount = _money(payload.get("discount_amount", "0"))
    total = _money(subtotal - discount_amount + tax)

    order = SalesOrder(
        order_number=await _next_order_number(db),
        customer_id=cust.id,
        employee_id=employee.id,
        quote_id=payload.get("quote_id"),
        line_items=line_items,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax,
        total_amount=total,
        payment_terms=payload.get("payment_terms"),
        status="pending",
        placed_at=_now(),
    )
    db.add(order)

    # If associated to a quote, mark it accepted.
    if payload.get("quote_id"):
        quote = await get_quote(db, payload["quote_id"])
        quote.status = "accepted"

    await db.commit()
    await db.refresh(order)
    return order


async def list_orders(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    employee_ids: Optional[set[int]] = None,
) -> Sequence[SalesOrder]:
    stmt = select(SalesOrder)
    if employee_ids is not None:
        stmt = stmt.where(SalesOrder.employee_id.in_(employee_ids or {-1}))
    if employee_id is not None:
        stmt = stmt.where(SalesOrder.employee_id == employee_id)
    if customer_id is not None:
        stmt = stmt.where(SalesOrder.customer_id == customer_id)
    if status:
        stmt = stmt.where(SalesOrder.status == status)
    stmt = stmt.order_by(SalesOrder.placed_at.desc())
    return (await db.execute(stmt)).scalars().all()


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    *,
    status: str,
    tracking_number: Optional[str] = None,
) -> SalesOrder:
    order = (
        await db.execute(select(SalesOrder).where(SalesOrder.id == order_id))
    ).scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")
    order.status = status
    if tracking_number:
        order.tracking_number = tracking_number
    if status == "delivered":
        order.delivered_at = _now()
        # Roll up to active sales target.
        await _apply_order_to_target(db, order)
    await db.commit()
    await db.refresh(order)
    return order


async def _apply_order_to_target(db: AsyncSession, order: SalesOrder) -> None:
    today = _now().date()
    target = (
        await db.execute(
            select(SalesTarget)
            .where(SalesTarget.employee_id == order.employee_id)
            .where(SalesTarget.period_start <= today)
            .where(SalesTarget.period_end >= today)
        )
    ).scalar_one_or_none()
    if target:
        target.achieved_amount = _money(
            target.achieved_amount + order.total_amount
        )


# ── Targets ──────────────────────────────────────────────────────────
async def create_target(db: AsyncSession, *, payload: dict) -> SalesTarget:
    if payload["period_end"] <= payload["period_start"]:
        raise ValidationError("period_end must be after period_start")
    t = SalesTarget(**payload)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


async def list_targets(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    period_type: Optional[str] = None,
    from_date=None,
    to_date=None,
    employee_ids: Optional[set[int]] = None,
) -> Sequence[SalesTarget]:
    stmt = select(SalesTarget)
    if employee_ids is not None:
        stmt = stmt.where(SalesTarget.employee_id.in_(employee_ids or {-1}))
    if employee_id is not None:
        stmt = stmt.where(SalesTarget.employee_id == employee_id)
    if period_type:
        stmt = stmt.where(SalesTarget.period_type == period_type)
    if from_date is not None:
        stmt = stmt.where(SalesTarget.period_end >= from_date)
    if to_date is not None:
        stmt = stmt.where(SalesTarget.period_start <= to_date)
    stmt = stmt.order_by(SalesTarget.period_start.desc())
    rows = (await db.execute(stmt)).scalars().all()
    # Decorate with achievement_pct so the admin list renders progress
    # bars without doing the math client-side.
    for t in rows:
        try:
            t.achievement_pct = (
                round(float(t.achieved_amount / t.target_amount * 100), 2)
                if t.target_amount and t.target_amount > 0
                else 0.0
            )
        except Exception:
            t.achievement_pct = 0.0
    return rows


async def update_target(
    db: AsyncSession, target_id: int, *, payload: dict
) -> SalesTarget:
    t = (
        await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Target not found")
    allowed = {
        "period_type", "period_start", "period_end",
        "target_amount", "commission_pct", "notes",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return t


async def delete_target(db: AsyncSession, target_id: int) -> None:
    t = (
        await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Target not found")
    await db.delete(t)
    await db.commit()


async def recompute_target_achievement(
    db: AsyncSession, target_id: int
) -> SalesTarget:
    """Recompute achieved_amount from actual records.

    Source of truth: SalesOrders for the assigned employee inside the
    target's period (most accurate). Falls back to summing won leads'
    expected_value when no orders exist, so a quick lead-driven
    pipeline still shows progress."""
    from datetime import datetime as _dt, time as _time
    from sqlalchemy import func as _f
    from app.models import Lead as _Lead, SalesOrder as _Order

    t = (
        await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Target not found")

    period_start_dt = _dt.combine(t.period_start, _time.min)
    period_end_dt = _dt.combine(t.period_end, _time.max)

    # Primary: confirmed/delivered orders inside the period.
    orders_total = (
        await db.execute(
            select(_f.coalesce(_f.sum(_Order.total_amount), 0))
            .where(_Order.employee_id == t.employee_id)
            .where(_Order.placed_at >= period_start_dt)
            .where(_Order.placed_at <= period_end_dt)
            .where(_Order.status != "cancelled")
        )
    ).scalar() or 0

    achieved = Decimal(str(orders_total))

    # Secondary: won leads inside the period (only if no orders).
    # Pending / rejected wins do NOT count.
    if achieved == 0:
        from sqlalchemy import or_ as _or
        won_total = (
            await db.execute(
                select(_f.coalesce(_f.sum(_Lead.expected_value), 0))
                .where(_Lead.assigned_to == t.employee_id)
                .where(_Lead.stage == "won")
                .where(
                    _or(
                        _Lead.won_approval_status.is_(None),
                        _Lead.won_approval_status == "approved",
                    )
                )
                .where(_Lead.expected_close_date >= t.period_start)
                .where(_Lead.expected_close_date <= t.period_end)
            )
        ).scalar() or 0
        achieved = Decimal(str(won_total))

    t.achieved_amount = _money(achieved)
    await db.commit()
    await db.refresh(t)
    # Decorate for response
    try:
        t.achievement_pct = (
            round(float(t.achieved_amount / t.target_amount * 100), 2)
            if t.target_amount and t.target_amount > 0
            else 0.0
        )
    except Exception:
        t.achievement_pct = 0.0
    return t


async def current_target_for(
    db: AsyncSession, employee_id: int
) -> Optional[SalesTarget]:
    today = _now().date()
    return (
        await db.execute(
            select(SalesTarget)
            .where(SalesTarget.employee_id == employee_id)
            .where(SalesTarget.period_start <= today)
            .where(SalesTarget.period_end >= today)
            .order_by(SalesTarget.period_start.desc())
        )
    ).scalar_one_or_none()


def target_summary(target: SalesTarget) -> dict:
    pct = (
        float(target.achieved_amount / target.target_amount * 100)
        if target.target_amount > 0
        else 0.0
    )
    commission = _money(target.achieved_amount * target.commission_pct / Decimal("100"))
    return {
        "target": target,
        "achievement_pct": round(pct, 2),
        "commission_amount": commission,
    }


# ── Promotions ───────────────────────────────────────────────────────
async def create_promotion(
    db: AsyncSession, *, employee: Employee, payload: dict
) -> PromotionActivity:
    p = PromotionActivity(employee_id=employee.id, **payload)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def list_promotions(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Sequence[PromotionActivity]:
    stmt = select(PromotionActivity)
    if employee_id is not None:
        stmt = stmt.where(PromotionActivity.employee_id == employee_id)
    if from_date:
        stmt = stmt.where(PromotionActivity.activity_date >= from_date)
    if to_date:
        stmt = stmt.where(PromotionActivity.activity_date <= to_date)
    stmt = stmt.order_by(PromotionActivity.activity_date.desc())
    return (await db.execute(stmt)).scalars().all()

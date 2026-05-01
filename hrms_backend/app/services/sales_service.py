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
    limit: int = 200,
) -> Sequence[Lead]:
    stmt = select(Lead)
    if assigned_to is not None:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
    if stage:
        stmt = stmt.where(Lead.stage == stage)
    stmt = stmt.order_by(Lead.created_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


async def get_lead(db: AsyncSession, lead_id: int) -> Lead:
    lead = (
        await db.execute(select(Lead).where(Lead.id == lead_id))
    ).scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead not found")
    return lead


async def update_lead_stage(
    db: AsyncSession,
    lead_id: int,
    *,
    stage: str,
    lost_reason: Optional[str] = None,
) -> Lead:
    lead = await get_lead(db, lead_id)
    if lead.stage == stage:
        return lead
    if stage == "lost" and not lost_reason:
        raise ValidationError("lost_reason is required when marking a lead as lost")
    lead.stage = stage
    lead.score = _STAGE_SCORE.get(stage, lead.score)
    if stage == "lost":
        lead.lost_reason = lost_reason
    await db.commit()
    await db.refresh(lead)
    return lead


async def pipeline_kanban(
    db: AsyncSession, *, assigned_to: Optional[int] = None
) -> list[dict]:
    stages = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]
    leads = await list_leads(db, assigned_to=assigned_to, limit=500)
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
) -> Sequence[SalesOrder]:
    stmt = select(SalesOrder)
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
) -> Sequence[SalesTarget]:
    stmt = select(SalesTarget)
    if employee_id is not None:
        stmt = stmt.where(SalesTarget.employee_id == employee_id)
    stmt = stmt.order_by(SalesTarget.period_start.desc())
    return (await db.execute(stmt)).scalars().all()


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

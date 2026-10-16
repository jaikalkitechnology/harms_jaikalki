from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Customer, User
from app.schemas.sales import (
    LeadActivityOut,
    LeadCommentCreate,
    LeadCreate,
    LeadOut,
    LeadStageUpdate,
    LeadUpdate,
    OrderCreate,
    OrderOut,
    OrderStatusUpdate,
    PipelineColumn,
    ProductCreate,
    ProductOut,
    PromotionCreate,
    PromotionOut,
    QuoteCreate,
    QuoteOut,
    QuoteStatusUpdate,
    SalesTargetCreate,
    SalesTargetOut,
    SalesTargetSummary,
    SalesTargetUpdate,
    WonDecision,
)
from app.services import employee_service as emp_svc
from app.services import sales_service as sales_svc
from app.services.quote_pdf import render_quote_pdf
from sqlalchemy import select

router = APIRouter(prefix="/sales", tags=["sales"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


async def _team(db: AsyncSession, user: User) -> Optional[set[int]]:
    """Whose sales the caller sees: everyone (Director / HR / Admin), or
    themselves and everyone below them."""
    return await emp_svc.visible_employee_ids(db, user)


async def _lead_for(db: AsyncSession, user: User, lead_id: int):
    """The lead, if it belongs to the caller's team (unassigned leads are
    open to managers so they can hand them out)."""
    lead = await sales_svc.get_lead(db, lead_id)
    team = await _team(db, user)
    if team is None or lead.assigned_to in team:
        return lead
    if lead.assigned_to is None and await emp_svc.has_reports(db, user):
        return lead
    raise NotFoundError("Lead not found")


async def _check_target_owner(db: AsyncSession, user: User, employee_id: int, *, write: bool) -> None:
    """Targets: you see your team's; you set them for the people below
    you (not yourself) unless you're Director / HR / Admin."""
    team = await _team(db, user)
    if team is None:
        return
    me = await emp_svc.get_self_employee(db, user)
    if employee_id not in team or (write and me and employee_id == me.id):
        raise NotFoundError("Employee not found")


async def _target_owner(db: AsyncSession, target_id: int) -> int:
    from app.models import SalesTarget

    owner = (
        await db.execute(select(SalesTarget.employee_id).where(SalesTarget.id == target_id))
    ).scalar_one_or_none()
    if owner is None:
        raise NotFoundError("Target not found")
    return owner


# ─── Leads ────────────────────────────────────────────────────────────
@router.get("/leads", response_model=list[LeadOut])
async def list_leads(
    stage: Optional[str] = None,
    source: Optional[str] = None,
    customer_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    search: Optional[str] = None,
    won_status: Optional[str] = Query(default=None),
    mine: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if mine:
        emp = await _self_employee(db, user)
        assigned_to = emp.id
    team = await _team(db, user)
    return await sales_svc.list_leads(
        db,
        assigned_in=team,
        include_unassigned=team is not None and await emp_svc.has_reports(db, user),
        assigned_to=assigned_to,
        stage=stage,
        source=source,
        customer_id=customer_id,
        search=search,
        won_status=won_status,
    )


@router.get("/leads/won-approvals", response_model=list[LeadOut])
async def list_pending_won_approvals(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    team = await _team(db, user)
    return [
        ld
        for ld in await sales_svc.list_pending_won_leads(db)
        if team is None or ld.assigned_to in team
    ]


@router.post(
    "/leads/{lead_id}/won-decision",
    response_model=LeadOut,
)
async def decide_won(
    lead_id: int,
    payload: WonDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    await _lead_for(db, user, lead_id)
    return await sales_svc.decide_won(
        db, lead_id,
        decision=payload.decision,
        reason=payload.reason,
        actor=user,
    )


@router.post(
    "/leads",
    response_model=LeadOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_lead(
    payload: LeadCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = payload.model_dump()
    if data.get("assigned_to") is None:
        emp = await emp_svc.get_self_employee(db, user)
        if emp:
            data["assigned_to"] = emp.id
    return await sales_svc.create_lead(db, payload=data)


@router.get("/leads/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _lead_for(db, user, lead_id)


@router.patch("/leads/{lead_id}/stage", response_model=LeadOut)
async def update_lead_stage(
    lead_id: int,
    payload: LeadStageUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _lead_for(db, user, lead_id)
    return await sales_svc.update_lead_stage(
        db, lead_id,
        stage=payload.stage,
        lost_reason=payload.lost_reason,
        actor=user,
    )


@router.put("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _lead_for(db, user, lead_id)
    return await sales_svc.update_lead(
        db, lead_id,
        payload=payload.model_dump(exclude_unset=True),
        actor=user,
    )


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    await _lead_for(db, user, lead_id)
    await sales_svc.delete_lead(db, lead_id)


# ── Lead activity timeline + comments ────────────────────────────────
@router.get("/leads/{lead_id}/activities", response_model=list[LeadActivityOut])
async def list_lead_activities(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _lead_for(db, user, lead_id)
    return await sales_svc.list_lead_activities(db, lead_id)


@router.post(
    "/leads/{lead_id}/comments",
    response_model=LeadActivityOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_lead_comment(
    lead_id: int,
    payload: LeadCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _lead_for(db, user, lead_id)
    return await sales_svc.add_lead_comment(
        db, lead_id, body=payload.body, actor=user
    )


@router.get("/pipeline", response_model=list[PipelineColumn])
async def pipeline(
    mine: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    assigned_to = None
    if mine:
        emp = await _self_employee(db, user)
        assigned_to = emp.id
    team = await _team(db, user)
    return await sales_svc.pipeline_kanban(
        db,
        assigned_to=assigned_to,
        assigned_in=team,
        include_unassigned=team is not None and await emp_svc.has_reports(db, user),
    )


# ─── Products ─────────────────────────────────────────────────────────
@router.get("/products", response_model=list[ProductOut])
async def list_products(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await sales_svc.list_products(db)


@router.post(
    "/products",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await sales_svc.create_product(db, payload=payload.model_dump())


# ─── Quotes ───────────────────────────────────────────────────────────
@router.get("/quotes", response_model=list[QuoteOut])
async def list_quotes(
    mine: bool = False,
    customer_id: Optional[int] = None,
    quote_status: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    employee_id = None
    if mine:
        emp = await _self_employee(db, user)
        employee_id = emp.id
    return await sales_svc.list_quotes(
        db,
        employee_id=employee_id,
        customer_id=customer_id,
        status=quote_status,
    )


@router.post(
    "/quotes",
    response_model=QuoteOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_quote(
    payload: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await sales_svc.create_quote(
        db, employee=emp, payload=payload.model_dump()
    )


@router.get("/quotes/{quote_id}", response_model=QuoteOut)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await sales_svc.get_quote(db, quote_id)


@router.patch("/quotes/{quote_id}/status", response_model=QuoteOut)
async def set_quote_status(
    quote_id: int,
    payload: QuoteStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await sales_svc.update_quote_status(
        db,
        quote_id,
        status=payload.status,
        signature_url=payload.signature_url,
    )


@router.get("/quotes/{quote_id}/pdf")
async def get_quote_pdf(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    quote = await sales_svc.get_quote(db, quote_id)
    cust = (
        await db.execute(select(Customer).where(Customer.id == quote.customer_id))
    ).scalar_one_or_none()
    if not cust:
        raise NotFoundError("Customer not found")
    from app.models import Employee

    emp = (
        await db.execute(select(Employee).where(Employee.id == quote.employee_id))
    ).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")
    pdf_bytes = render_quote_pdf(quote=quote, customer=cust, employee=emp)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{quote.quote_number.replace("/", "-")}.pdf"'
            )
        },
    )


# ─── Orders ───────────────────────────────────────────────────────────
@router.get("/orders", response_model=list[OrderOut])
async def list_orders(
    mine: bool = False,
    customer_id: Optional[int] = None,
    order_status: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    employee_id = None
    if mine:
        emp = await _self_employee(db, user)
        employee_id = emp.id
    return await sales_svc.list_orders(
        db,
        employee_ids=await _team(db, user),
        employee_id=employee_id,
        customer_id=customer_id,
        status=order_status,
    )


@router.post(
    "/orders",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await sales_svc.create_order(
        db, employee=emp, payload=payload.model_dump()
    )


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
async def set_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await sales_svc.update_order_status(
        db,
        order_id,
        status=payload.status,
        tracking_number=payload.tracking_number,
    )


# ─── Targets ──────────────────────────────────────────────────────────
@router.get("/targets/me", response_model=Optional[SalesTargetSummary])
async def my_target(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    target = await sales_svc.current_target_for(db, emp.id)
    if not target:
        return None
    return sales_svc.target_summary(target)


@router.get("/targets/me/all", response_model=list[SalesTargetSummary])
async def my_targets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """All my running targets (₹ sales, visits, verifications …)."""
    emp = await _self_employee(db, user)
    return [
        sales_svc.target_summary(t)
        for t in await sales_svc.current_targets_for(db, emp.id)
    ]


@router.get("/targets", response_model=list[SalesTargetOut])
async def list_targets(
    employee_id: Optional[int] = None,
    period_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await sales_svc.list_targets(
        db,
        employee_ids=await _team(db, user),
        employee_id=employee_id,
        period_type=period_type,
        from_date=from_date,
        to_date=to_date,
    )


@router.post(
    "/targets",
    response_model=SalesTargetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_target(
    payload: SalesTargetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    await _check_target_owner(db, user, payload.employee_id, write=True)
    return await sales_svc.create_target(db, payload=payload.model_dump())


@router.put("/targets/{target_id}", response_model=SalesTargetOut)
async def update_target(
    target_id: int,
    payload: SalesTargetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    await _check_target_owner(db, user, await _target_owner(db, target_id), write=True)
    return await sales_svc.update_target(
        db, target_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    await _check_target_owner(db, user, await _target_owner(db, target_id), write=True)
    await sales_svc.delete_target(db, target_id)


@router.post("/targets/{target_id}/recompute", response_model=SalesTargetOut)
async def recompute_target(
    target_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _check_target_owner(db, user, await _target_owner(db, target_id), write=False)
    return await sales_svc.recompute_target_achievement(db, target_id)


# ─── Promotions ───────────────────────────────────────────────────────
@router.post(
    "/promotions",
    response_model=PromotionOut,
    status_code=status.HTTP_201_CREATED,
)
async def log_promotion(
    payload: PromotionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await sales_svc.create_promotion(
        db, employee=emp, payload=payload.model_dump()
    )


@router.get("/promotions/me", response_model=list[PromotionOut])
async def my_promotions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await sales_svc.list_promotions(db, employee_id=emp.id)


@router.get("/promotions", response_model=list[PromotionOut])
async def list_all_promotions(
    employee_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await sales_svc.list_promotions(
        db,
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
    )

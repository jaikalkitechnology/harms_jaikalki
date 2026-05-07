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


# ─── Leads ────────────────────────────────────────────────────────────
@router.get("/leads", response_model=list[LeadOut])
async def list_leads(
    stage: Optional[str] = None,
    source: Optional[str] = None,
    customer_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    search: Optional[str] = None,
    mine: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if mine:
        emp = await _self_employee(db, user)
        assigned_to = emp.id
    return await sales_svc.list_leads(
        db,
        assigned_to=assigned_to,
        stage=stage,
        source=source,
        customer_id=customer_id,
        search=search,
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
    _: User = Depends(get_current_user),
):
    return await sales_svc.get_lead(db, lead_id)


@router.patch("/leads/{lead_id}/stage", response_model=LeadOut)
async def update_lead_stage(
    lead_id: int,
    payload: LeadStageUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
    return await sales_svc.update_lead(
        db, lead_id,
        payload=payload.model_dump(exclude_unset=True),
        actor=user,
    )


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    await sales_svc.delete_lead(db, lead_id)


# ── Lead activity timeline + comments ────────────────────────────────
@router.get("/leads/{lead_id}/activities", response_model=list[LeadActivityOut])
async def list_lead_activities(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
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
    return await sales_svc.pipeline_kanban(db, assigned_to=assigned_to)


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


@router.get("/targets", response_model=list[SalesTargetOut])
async def list_targets(
    employee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await sales_svc.list_targets(db, employee_id=employee_id)


@router.post(
    "/targets",
    response_model=SalesTargetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_target(
    payload: SalesTargetCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await sales_svc.create_target(db, payload=payload.model_dump())


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

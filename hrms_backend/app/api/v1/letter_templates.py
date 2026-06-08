"""HR letter / document template CRUD + per-employee generator."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import LetterTemplate, User
from app.schemas.letter_template import (
    COMMON_PLACEHOLDERS,
    LetterGenerateOptions,
    LetterPlaceholderHint,
    LetterTemplateCreate,
    LetterTemplateOut,
    LetterTemplateUpdate,
)
from app.services import employee_service as emp_svc
from app.services.letter_template_service import (
    render_letter_pdf,
    seed_default_templates,
)

router = APIRouter(tags=["letter-templates"])


# ── Templates CRUD (admin) ─────────────────────────────────────────────
@router.get(
    "/letter-templates",
    response_model=list[LetterTemplateOut],
)
async def list_templates(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # First time the page loads, lazily seed the bundled HR letters so
    # the admin sees the standard set out of the box.
    await seed_default_templates(db)
    stmt = select(LetterTemplate).order_by(LetterTemplate.name)
    if not include_inactive:
        stmt = stmt.where(LetterTemplate.is_active.is_(True))
    return (await db.execute(stmt)).scalars().all()


@router.get(
    "/letter-templates/placeholders",
    response_model=list[LetterPlaceholderHint],
)
async def list_placeholders(_: User = Depends(get_current_user)):
    """Suggested placeholders the renderer understands by default."""
    return COMMON_PLACEHOLDERS


@router.post(
    "/letter-templates",
    response_model=LetterTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    payload: LetterTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    code = payload.code.strip().lower()
    dup = (
        await db.execute(
            select(LetterTemplate).where(LetterTemplate.code == code)
        )
    ).scalar_one_or_none()
    if dup:
        raise ConflictError(f"Template code {code!r} already exists")
    obj = LetterTemplate(**{**payload.model_dump(), "code": code})
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/letter-templates/{template_id}",
    response_model=LetterTemplateOut,
)
async def update_template(
    template_id: int,
    payload: LetterTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(
            select(LetterTemplate).where(LetterTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Template not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/letter-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    obj = (
        await db.execute(
            select(LetterTemplate).where(LetterTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if obj:
        await db.delete(obj)
        await db.commit()


# ── Generate a letter for an employee ──────────────────────────────────
@router.post(
    "/employees/{employee_id}/letters/{template_id}/generate"
)
async def generate_letter(
    employee_id: int,
    template_id: int,
    options: Optional[LetterGenerateOptions] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    emp = await emp_svc.get_employee(db, employee_id)
    tmpl = (
        await db.execute(
            select(LetterTemplate).where(LetterTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not tmpl:
        raise NotFoundError("Template not found")

    overrides: dict = {}
    if options:
        if options.letter_no:
            overrides["letter_no"] = options.letter_no
        if options.on_date:
            overrides["date"] = options.on_date
        if options.last_working_date:
            overrides["last_working_date"] = options.last_working_date
        if options.ctc_amount:
            overrides["ctc_amount"] = options.ctc_amount
        if options.ctc_amount_words:
            overrides["ctc_amount_words"] = options.ctc_amount_words
        if options.overrides:
            overrides.update(options.overrides)

    pdf = render_letter_pdf(tmpl, emp, overrides=overrides)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{tmpl.code}_{emp.employee_code}.pdf"'
            ),
            "Cache-Control": "no-store",
        },
    )

"""Letterhead settings, issued employee letters and company policies.

- Letterhead: HR edits the header / footer text and logo printed on
  every generated letter (Settings → Letterhead).
- Letters: HR creates a letter from a template (saved as a PDF on the
  letterhead) or uploads a signed copy. Employees see the visible ones
  under More → Documents in the app.
- Policies: HR uploads policy documents; published ones are visible to
  everyone.
"""
from __future__ import annotations

import io
import mimetypes
from datetime import date, datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import (
    CompanyPolicy,
    Employee,
    EmployeeLetter,
    GeneratedDocument,
    LetterTemplate,
    Notification,
    User,
)
from app.models.hr_documents import LETTER_TYPES, POLICY_CATEGORIES
from app.schemas.hr_documents import (
    CompanyPolicyOut,
    CompanyPolicyUpdate,
    EmployeeLetterIssue,
    EmployeeLetterOut,
    EmployeeLetterUpdate,
    LetterheadOut,
    LetterheadUpdate,
)
from app.services import employee_service as emp_svc
from app.services import storage
from app.services.letter_template_service import (
    render_letter_pdf,
    render_letterhead_preview,
)
from app.services.letterhead import clean, get_letterhead, merge, set_letterhead

router = APIRouter(tags=["hr-documents"])

MANAGE = "employee.update"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DOC_MIME = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
LOGO_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_LOGO_BYTES = 2 * 1024 * 1024

# Template category → letter type on the employee's file.
_CATEGORY_TO_TYPE = {
    "offer": "offer",
    "appointment": "appointment",
    "confirmation": "confirmation",
    "experience": "experience",
    "increment": "increment",
    "termination": "termination",
    "warning": "warning",
}


def _now() -> datetime:
    return datetime.utcnow()


def _can_manage(user: User) -> bool:
    codes = user.permission_codes
    return MANAGE in codes or "system.config" in codes


async def _read_upload(
    file: UploadFile, *, allowed: set[str], max_bytes: int
) -> tuple[bytes, str, str]:
    """(contents, mime, filename) after type and size checks."""
    name = (file.filename or "upload").strip() or "upload"
    mime = (file.content_type or "").lower()
    if mime not in allowed:
        # Some browsers send octet-stream — fall back to the extension.
        mime = (mimetypes.guess_type(name)[0] or "").lower()
    if mime not in allowed:
        kinds = ", ".join(sorted(m.split("/")[1].upper() for m in allowed))
        raise ValidationError(f"Unsupported file type — upload {kinds}")
    contents = await file.read()
    if not contents:
        raise ValidationError("The file is empty")
    if len(contents) > max_bytes:
        raise ValidationError(f"File too large (max {max_bytes // (1024 * 1024)} MB)")
    return contents, mime, name


def _file_response(data: bytes, mime: str, filename: str) -> Response:
    safe = filename.replace('"', "").replace("\n", " ")
    return Response(
        content=data,
        media_type=mime,
        headers={
            "Content-Disposition": f'inline; filename="{safe}"',
            "Cache-Control": "no-store",
        },
    )


def _load(key: str) -> bytes:
    try:
        return storage.read_bytes(key)
    except FileNotFoundError as exc:
        raise NotFoundError("The file is missing from storage") from exc


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise ValidationError(f"Invalid date: {raw}") from exc


async def _notify_employee(
    db: AsyncSession, emp: Employee, *, type: str, title: str, body: str, data: dict
) -> None:
    if not emp.user_id:
        return
    db.add(
        Notification(
            user_id=emp.user_id,
            channel="in_app",
            type=type,
            title=title,
            body=body,
            data=data,
            sent_at=_now(),
            status="sent",
        )
    )


# ── Letterhead ───────────────────────────────────────────────────────
def _letterhead_out(cfg: dict) -> LetterheadOut:
    return LetterheadOut(
        **{k: v for k, v in cfg.items() if k != "logo_key"},
        has_custom_logo=bool(cfg.get("logo_key")),
    )


@router.get("/letterhead", response_model=LetterheadOut)
async def read_letterhead(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    return _letterhead_out(await get_letterhead(db))


@router.put("/letterhead", response_model=LetterheadOut)
async def update_letterhead(
    payload: LetterheadUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    changes = clean(payload.model_dump(exclude_unset=True))
    if "company_name" in changes and not changes["company_name"]:
        raise ValidationError("Company name can't be empty")
    return _letterhead_out(await set_letterhead(db, changes, actor=user))


@router.post("/letterhead/logo", response_model=LetterheadOut)
async def upload_letterhead_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    contents, mime, name = await _read_upload(
        file, allowed=LOGO_MIME, max_bytes=MAX_LOGO_BYTES
    )
    # Make sure ReportLab can actually draw it before we keep it.
    from reportlab.lib.utils import ImageReader

    try:
        ImageReader(io.BytesIO(contents)).getSize()
    except Exception as exc:
        raise ValidationError("That image couldn't be read") from exc
    old = (await get_letterhead(db)).get("logo_key")
    key, _url = storage.upload_fileobj(
        io.BytesIO(contents),
        key_prefix="letterhead",
        filename=name,
        content_type=mime,
    )
    cfg = await set_letterhead(db, {"logo_key": key}, actor=user)
    if old and old != key:
        storage.delete(old)
    return _letterhead_out(cfg)


@router.delete("/letterhead/logo", response_model=LetterheadOut)
async def reset_letterhead_logo(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    """Go back to the bundled Jaikalki logo."""
    old = (await get_letterhead(db)).get("logo_key")
    cfg = await set_letterhead(db, {"logo_key": None}, actor=user)
    if old:
        storage.delete(old)
    return _letterhead_out(cfg)


@router.get("/letterhead/logo")
async def letterhead_logo(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    key = (await get_letterhead(db)).get("logo_key")
    if not key:
        raise NotFoundError("No custom logo uploaded")
    data = _load(key)
    mime = mimetypes.guess_type(key)[0] or "image/png"
    return _file_response(data, mime, key.rsplit("/", 1)[-1])


@router.post("/letterhead/preview")
async def preview_letterhead(
    payload: Optional[LetterheadUpdate] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    """Sample letter on the saved letterhead, with any unsaved edits in
    the body applied on top."""
    cfg = await get_letterhead(db)
    if payload:
        cfg = merge({**cfg, **clean(payload.model_dump(exclude_unset=True))})
    return _file_response(
        render_letterhead_preview(cfg), "application/pdf", "letterhead-preview.pdf"
    )


# ── Employee letters ─────────────────────────────────────────────────
_LEGACY_TYPES = {
    "offer_letter": ("offer", "Offer letter"),
    "confirmation_letter": ("confirmation", "Confirmation letter"),
}


async def _carry_over_generated(db: AsyncSession, employee_id: int) -> None:
    """Bring offer / confirmation letters generated by the payroll flow
    (generated_documents) onto the employee's letter file, once each."""
    docs = (
        await db.execute(
            select(GeneratedDocument).where(
                GeneratedDocument.employee_id == employee_id,
                GeneratedDocument.doc_type.in_(list(_LEGACY_TYPES)),
            )
        )
    ).scalars().all()
    if not docs:
        return
    seen = set(
        (
            await db.execute(
                select(EmployeeLetter.generated_document_id).where(
                    EmployeeLetter.generated_document_id.in_([d.id for d in docs])
                )
            )
        ).scalars().all()
    )
    added = False
    for d in docs:
        if d.id in seen:
            continue
        key = storage.key_from_url(d.file_url)
        if not key:
            continue  # never reached storage — nothing to download
        letter_type, title = _LEGACY_TYPES[d.doc_type]
        issued = _parse_date((d.payload or {}).get("letter_date")) if d.payload else None
        db.add(
            EmployeeLetter(
                employee_id=employee_id,
                letter_type=letter_type,
                title=title,
                letter_number=d.letter_number,
                issued_on=issued or (d.created_at.date() if d.created_at else date.today()),
                source="generated",
                generated_document_id=d.id,
                file_key=key,
                file_name=f"{(d.letter_number or title).replace('/', '-')}.pdf",
                mime_type="application/pdf",
                visible_to_employee=True,
                issued_by=d.generated_by,
            )
        )
        added = True
    if added:
        await db.commit()


async def _letters_for(
    db: AsyncSession, employee_id: int, *, visible_only: bool
) -> list[EmployeeLetter]:
    await _carry_over_generated(db, employee_id)
    stmt = select(EmployeeLetter).where(
        EmployeeLetter.employee_id == employee_id,
        EmployeeLetter.is_removed.is_(False),
    )
    if visible_only:
        stmt = stmt.where(EmployeeLetter.visible_to_employee.is_(True))
    stmt = stmt.order_by(EmployeeLetter.issued_on.desc(), EmployeeLetter.id.desc())
    return list((await db.execute(stmt)).scalars().all())


async def _get_letter(db: AsyncSession, letter_id: int) -> EmployeeLetter:
    obj = (
        await db.execute(
            select(EmployeeLetter).where(
                EmployeeLetter.id == letter_id,
                EmployeeLetter.is_removed.is_(False),
            )
        )
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Letter not found")
    return obj


@router.get(
    "/employees/{employee_id}/issued-letters",
    response_model=list[EmployeeLetterOut],
)
async def list_employee_letters(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    await emp_svc.get_employee(db, employee_id)
    return await _letters_for(db, employee_id, visible_only=False)


@router.post(
    "/employees/{employee_id}/issued-letters/from-template/{template_id}",
    response_model=EmployeeLetterOut,
    status_code=status.HTTP_201_CREATED,
)
async def issue_letter_from_template(
    employee_id: int,
    template_id: int,
    payload: EmployeeLetterIssue,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    emp = await emp_svc.get_employee(db, employee_id)
    tmpl = (
        await db.execute(select(LetterTemplate).where(LetterTemplate.id == template_id))
    ).scalar_one_or_none()
    if not tmpl:
        raise NotFoundError("Template not found")

    issued_on = payload.on_date or date.today()
    overrides: dict = {"date": issued_on.strftime("%d %b %Y")}
    if payload.letter_no:
        overrides["letter_no"] = payload.letter_no
    for k in ("last_working_date", "ctc_amount", "ctc_amount_words"):
        v = getattr(payload, k)
        if v:
            overrides[k] = v
    if payload.overrides:
        overrides.update(payload.overrides)

    pdf = render_letter_pdf(
        tmpl, emp, overrides=overrides, letterhead=await get_letterhead(db)
    )
    filename = f"{tmpl.code}_{emp.employee_code}.pdf"
    key, _url = storage.upload_fileobj(
        io.BytesIO(pdf),
        key_prefix=f"employees/{emp.employee_code}/letters",
        filename=filename,
        content_type="application/pdf",
    )
    letter = EmployeeLetter(
        employee_id=emp.id,
        letter_type=payload.letter_type or _CATEGORY_TO_TYPE.get(tmpl.category, "other"),
        title=(payload.title or tmpl.name).strip(),
        letter_number=payload.letter_no,
        issued_on=issued_on,
        source="generated",
        template_id=tmpl.id,
        file_key=key,
        file_name=filename,
        mime_type="application/pdf",
        file_size=len(pdf),
        visible_to_employee=payload.visible_to_employee,
        notes=payload.notes,
        issued_by=user.id,
    )
    db.add(letter)
    await db.flush()
    if letter.visible_to_employee:
        await _notify_employee(
            db, emp,
            type="letter_issued",
            title=f"New letter: {letter.title}",
            body="It's in More → Documents in the app.",
            data={"letter_id": letter.id},
        )
    await db.commit()
    await db.refresh(letter)
    return letter


@router.post(
    "/employees/{employee_id}/issued-letters/upload",
    response_model=EmployeeLetterOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_employee_letter(
    employee_id: int,
    letter_type: str = Form(...),
    title: str = Form(...),
    letter_number: Optional[str] = Form(default=None),
    issued_on: Optional[str] = Form(default=None),
    visible_to_employee: bool = Form(default=True),
    notes: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    if letter_type not in LETTER_TYPES:
        raise ValidationError(f"letter_type must be one of: {', '.join(LETTER_TYPES)}")
    title = title.strip()
    if len(title) < 2:
        raise ValidationError("Give the letter a title")
    emp = await emp_svc.get_employee(db, employee_id)
    contents, mime, name = await _read_upload(file, allowed=DOC_MIME, max_bytes=MAX_BYTES)
    key, _url = storage.upload_fileobj(
        io.BytesIO(contents),
        key_prefix=f"employees/{emp.employee_code}/letters",
        filename=name,
        content_type=mime,
    )
    letter = EmployeeLetter(
        employee_id=emp.id,
        letter_type=letter_type,
        title=title[:200],
        letter_number=(letter_number or "").strip()[:64] or None,
        issued_on=_parse_date(issued_on) or date.today(),
        source="uploaded",
        file_key=key,
        file_name=name[:255],
        mime_type=mime,
        file_size=len(contents),
        visible_to_employee=visible_to_employee,
        notes=(notes or "").strip()[:500] or None,
        issued_by=user.id,
    )
    db.add(letter)
    await db.flush()
    if letter.visible_to_employee:
        await _notify_employee(
            db, emp,
            type="letter_issued",
            title=f"New letter: {letter.title}",
            body="It's in More → Documents in the app.",
            data={"letter_id": letter.id},
        )
    await db.commit()
    await db.refresh(letter)
    return letter


@router.patch("/issued-letters/{letter_id}", response_model=EmployeeLetterOut)
async def update_employee_letter(
    letter_id: int,
    payload: EmployeeLetterUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    letter = await _get_letter(db, letter_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        if v is None and k in ("letter_type", "title", "issued_on", "visible_to_employee"):
            continue
        setattr(letter, k, v)
    await db.commit()
    await db.refresh(letter)
    return letter


@router.delete("/issued-letters/{letter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_letter(
    letter_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    letter = await _get_letter(db, letter_id)
    if letter.generated_document_id:
        # Keep the payroll record (letter numbering); just drop it here.
        letter.is_removed = True
        await db.commit()
        return
    key = letter.file_key
    await db.delete(letter)
    await db.commit()
    storage.delete(key)


@router.get("/issued-letters/{letter_id}/file")
async def download_employee_letter(
    letter_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    letter = await _get_letter(db, letter_id)
    if not _can_manage(user):
        me = await emp_svc.get_self_employee(db, user)
        if not me or me.id != letter.employee_id or not letter.visible_to_employee:
            raise ForbiddenError("Not allowed to open this letter")
    return _file_response(_load(letter.file_key), letter.mime_type, letter.file_name)


@router.get("/me/letters", response_model=list[EmployeeLetterOut])
async def my_letters(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    me = await emp_svc.get_self_employee(db, user)
    if not me:
        return []
    return await _letters_for(db, me.id, visible_only=True)


# ── Company policies ─────────────────────────────────────────────────
async def _get_policy(db: AsyncSession, policy_id: int) -> CompanyPolicy:
    obj = (
        await db.execute(select(CompanyPolicy).where(CompanyPolicy.id == policy_id))
    ).scalar_one_or_none()
    if not obj:
        raise NotFoundError("Policy not found")
    return obj


async def _announce_policy(db: AsyncSession, policy: CompanyPolicy) -> None:
    """In-app notification to everyone with an app login."""
    user_ids = (
        await db.execute(
            select(Employee.user_id).where(
                Employee.user_id.is_not(None),
                Employee.status.not_in(
                    ("resigned", "terminated", "separated", "inactive")
                ),
            )
        )
    ).scalars().all()
    for uid in set(user_ids):
        db.add(
            Notification(
                user_id=uid,
                channel="in_app",
                type="policy_published",
                title=f"New policy: {policy.title}",
                body="Read it in More → Documents in the app.",
                data={"policy_id": policy.id},
                sent_at=_now(),
                status="sent",
            )
        )


@router.get("/policies", response_model=list[CompanyPolicyOut])
async def list_policies(
    include_unpublished: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Published policies for everyone; HR can include drafts."""
    stmt = select(CompanyPolicy)
    if not (include_unpublished and _can_manage(user)):
        stmt = stmt.where(CompanyPolicy.is_published.is_(True))
    stmt = stmt.order_by(
        CompanyPolicy.effective_date.desc(), CompanyPolicy.id.desc()
    )
    return (await db.execute(stmt)).scalars().all()


@router.post(
    "/policies",
    response_model=CompanyPolicyOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_policy(
    title: str = Form(...),
    category: str = Form(default="hr"),
    description: Optional[str] = Form(default=None),
    version: Optional[str] = Form(default=None),
    effective_date: Optional[str] = Form(default=None),
    is_published: bool = Form(default=True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(MANAGE)),
):
    title = title.strip()
    if len(title) < 2:
        raise ValidationError("Give the policy a title")
    if category not in POLICY_CATEGORIES:
        raise ValidationError(f"category must be one of: {', '.join(POLICY_CATEGORIES)}")
    contents, mime, name = await _read_upload(file, allowed=DOC_MIME, max_bytes=MAX_BYTES)
    key, _url = storage.upload_fileobj(
        io.BytesIO(contents),
        key_prefix="policies",
        filename=name,
        content_type=mime,
    )
    policy = CompanyPolicy(
        title=title[:200],
        category=category,
        description=(description or "").strip()[:4000] or None,
        version=(version or "").strip()[:32] or None,
        effective_date=_parse_date(effective_date),
        file_key=key,
        file_name=name[:255],
        mime_type=mime,
        file_size=len(contents),
        is_published=is_published,
        uploaded_by=user.id,
    )
    db.add(policy)
    await db.flush()
    if policy.is_published:
        await _announce_policy(db, policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.patch("/policies/{policy_id}", response_model=CompanyPolicyOut)
async def update_policy(
    policy_id: int,
    payload: CompanyPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    policy = await _get_policy(db, policy_id)
    was_published = policy.is_published
    for k, v in payload.model_dump(exclude_unset=True).items():
        if v is None and k in ("title", "category", "is_published"):
            continue
        setattr(policy, k, v)
    if policy.is_published and not was_published:
        await _announce_policy(db, policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.put("/policies/{policy_id}/file", response_model=CompanyPolicyOut)
async def replace_policy_file(
    policy_id: int,
    file: UploadFile = File(...),
    version: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    """Upload a revised document for the same policy."""
    policy = await _get_policy(db, policy_id)
    contents, mime, name = await _read_upload(file, allowed=DOC_MIME, max_bytes=MAX_BYTES)
    key, _url = storage.upload_fileobj(
        io.BytesIO(contents),
        key_prefix="policies",
        filename=name,
        content_type=mime,
    )
    old = policy.file_key
    policy.file_key = key
    policy.file_name = name[:255]
    policy.mime_type = mime
    policy.file_size = len(contents)
    if version is not None and version.strip():
        policy.version = version.strip()[:32]
    await db.commit()
    await db.refresh(policy)
    storage.delete(old)
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(MANAGE)),
):
    policy = await _get_policy(db, policy_id)
    key = policy.file_key
    await db.delete(policy)
    await db.commit()
    storage.delete(key)


@router.get("/policies/{policy_id}/file")
async def download_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    policy = await _get_policy(db, policy_id)
    if not policy.is_published and not _can_manage(user):
        raise NotFoundError("Policy not found")
    return _file_response(_load(policy.file_key), policy.mime_type, policy.file_name)

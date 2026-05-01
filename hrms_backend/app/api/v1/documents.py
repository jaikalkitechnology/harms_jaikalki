from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.dependencies import get_current_user, get_db
from app.models import Employee, EmployeeDocument, User
from app.schemas.employee import DocumentOut
from app.services import employee_service as svc
from app.services.storage import signed_url, upload_fileobj

router = APIRouter(tags=["documents"])

ALLOWED_DOC_TYPES = {
    "aadhaar",
    "pan",
    "passport",
    "education",
    "experience",
    "offer_letter",
    "confirmation_letter",
    "address_proof",
    "photo",
    "other",
}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _can_modify(user: User, emp: Employee) -> bool:
    if svc.can_see_all(user):
        return True
    return emp.user_id == user.id


@router.get(
    "/employees/{employee_id}/documents",
    response_model=list[DocumentOut],
)
async def list_documents(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await svc.get_employee(db, employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    return (
        await db.execute(
            select(EmployeeDocument)
            .where(EmployeeDocument.employee_id == employee_id)
            .order_by(EmployeeDocument.created_at.desc())
        )
    ).scalars().all()


@router.post(
    "/employees/{employee_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    employee_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if doc_type not in ALLOWED_DOC_TYPES:
        raise ValidationError(f"doc_type must be one of: {sorted(ALLOWED_DOC_TYPES)}")
    if file.content_type and file.content_type not in ALLOWED_MIME:
        raise ValidationError(f"Unsupported content type: {file.content_type}")

    emp = await svc.get_employee(db, employee_id)
    if not _can_modify(user, emp):
        raise ForbiddenError("Cannot upload documents for this employee")

    # Read & enforce size limit.
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise ValidationError("File too large (max 10 MB)")

    import io
    key, url = upload_fileobj(
        io.BytesIO(contents),
        key_prefix=f"employees/{emp.employee_code}/{doc_type}",
        filename=file.filename or "upload",
        content_type=file.content_type,
    )

    doc = EmployeeDocument(
        employee_id=emp.id,
        doc_type=doc_type,
        file_name=file.filename or "upload",
        file_url=url,
        file_size=len(contents),
        mime_type=file.content_type,
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/documents/{document_id}/signed-url")
async def get_signed_url(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = (
        await db.execute(
            select(EmployeeDocument).where(EmployeeDocument.id == document_id)
        )
    ).scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document not found")
    emp = await svc.get_employee(db, doc.employee_id)
    allowed = await svc.visible_employee_ids(db, user)
    svc.assert_can_view(user, emp, allowed)
    # Extract object key from URL.
    from app.config import settings
    base = f"{settings.S3_ENDPOINT.rstrip('/')}/{settings.S3_BUCKET}/"
    key = doc.file_url[len(base):] if doc.file_url.startswith(base) else doc.file_url
    return {"url": signed_url(key)}

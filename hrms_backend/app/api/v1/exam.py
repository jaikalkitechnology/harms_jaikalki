from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from app.models import Employee, User
from app.schemas.exam import (
    CERTIFICATE_TYPES,
    AttemptDetail,
    AttemptResult,
    AttemptSubmitRequest,
    CertificateCreate,
    CertificateOut,
    CertificateRevoke,
    CertificateUpdate,
    CertificateVerifyResponse,
    ExamCreate,
    ExamOut,
    ExamPublishUpdate,
    ExamSummary,
    ExamUpdate,
    FlagSubmit,
    QuestionCreate,
    QuestionOut,
    QuestionPublic,
    QuestionUpdate,
    StartAttemptResponse,
)
from app.services import employee_service as emp_svc
from app.services import exam_service as exam_svc
from app.services.certificate_pdf import render_certificate

router = APIRouter(prefix="/exams", tags=["exams"])


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ─── Question bank ────────────────────────────────────────────────────
@router.get("/questions", response_model=list[QuestionOut])
async def list_questions(
    department_id: Optional[int] = None,
    course_id: Optional[int] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await exam_svc.list_questions(
        db,
        department_id=department_id,
        course_id=course_id,
        topic=topic,
        difficulty=difficulty,
        status=status if status else "active",
    )


def _wrap_db_call(coro):
    """Translate a missing-column / Unknown-column DB error into a
    503 with an actionable message, instead of an opaque 500. Lets
    the admin web display "schema needs migration" toast cleanly."""
    from fastapi import HTTPException
    from sqlalchemy.exc import DBAPIError, OperationalError

    async def _run():
        try:
            return await coro
        except (OperationalError, DBAPIError) as e:
            msg = str(e).lower()
            if "unknown column" in msg or "no such column" in msg:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "DB schema is out of date — run the column "
                        "migration. See backend logs for the SQL."
                    ),
                ) from e
            raise

    return _run()


@router.post(
    "/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await _wrap_db_call(
        exam_svc.create_question(db, payload=payload.model_dump())
    )


@router.put("/questions/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: int,
    payload: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await _wrap_db_call(
        exam_svc.update_question(
            db, question_id, payload=payload.model_dump(exclude_unset=True)
        )
    )


@router.delete(
    "/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    await exam_svc.delete_question(db, question_id)


@router.put("/questions/{question_id}/options", response_model=QuestionOut)
async def replace_question_options(
    question_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    """Replace the option list on a saved question — used to fix the
    correct answer post-creation. Body: {"options": [...]}"""
    options = body.get("options") or []
    return await _wrap_db_call(
        exam_svc.replace_question_options(
            db, question_id, options=options
        )
    )


# ─── Exams ────────────────────────────────────────────────────────────
@router.get("/", response_model=list[ExamSummary])
async def list_exams(
    course_id: Optional[int] = None,
    exam_type: Optional[str] = None,
    include_unpublished: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_drafts = False
    if include_unpublished:
        from app.core.permissions import Role as RoleEnum
        if set(user.role_codes) & {
            RoleEnum.SUPER_ADMIN.value,
            RoleEnum.HR.value,
            RoleEnum.ADMIN.value,
            RoleEnum.DIRECTOR.value,
        }:
            show_drafts = True
    return await exam_svc.list_exams(
        db,
        course_id=course_id,
        exam_type=exam_type,
        published_only=not show_drafts,
    )


@router.post(
    "/",
    response_model=ExamOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_exam(
    payload: ExamCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await exam_svc.create_exam(db, payload=payload.model_dump())


# ─── Certificate admin endpoints (declared before /{exam_id} so the
# generic exam-id catcher doesn't swallow `/certificates`). ─────────
from datetime import date as _date  # noqa: E402


@router.get("/certificates", response_model=list[CertificateOut])
async def list_certificates(
    employee_id: Optional[int] = None,
    course_id: Optional[int] = None,
    is_revoked: Optional[bool] = None,
    search: Optional[str] = None,
    from_date: Optional[_date] = None,
    to_date: Optional[_date] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await exam_svc.list_certificates(
        db,
        employee_id=employee_id,
        course_id=course_id,
        is_revoked=is_revoked,
        search=search,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/certificates",
    response_model=CertificateOut,
    status_code=status.HTTP_201_CREATED,
)
async def issue_certificate_admin(
    payload: CertificateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await exam_svc.admin_issue_certificate(
        db, payload=payload.model_dump()
    )


@router.post(
    "/certificates/upload",
    response_model=CertificateOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_certificate_admin(
    employee_id: int = Form(...),
    title: str = Form(...),
    certificate_type: str = Form(default="appreciation"),
    issued_date: Optional[_date] = Form(default=None),
    body_text: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    """Put a ready-made certificate (scanned / designed elsewhere) on the
    employee's record. The PDF endpoint serves this file as-is."""
    import io
    import mimetypes

    from app.core.exceptions import ValidationError
    from app.services import storage

    if certificate_type not in CERTIFICATE_TYPES:
        raise ValidationError(
            f"certificate_type must be one of: {', '.join(CERTIFICATE_TYPES)}"
        )
    title = title.strip()
    if len(title) < 2:
        raise ValidationError("Give the certificate a title")
    allowed = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
    name = (file.filename or "certificate").strip() or "certificate"
    mime = (file.content_type or "").lower()
    if mime not in allowed:
        mime = (mimetypes.guess_type(name)[0] or "").lower()
    if mime not in allowed:
        raise ValidationError("Upload a PDF, JPG, PNG or WEBP file")
    contents = await file.read()
    if not contents:
        raise ValidationError("The file is empty")
    if len(contents) > 10 * 1024 * 1024:
        raise ValidationError("File too large (max 10 MB)")
    emp = await emp_svc.get_employee(db, employee_id)
    key, _url = storage.upload_fileobj(
        io.BytesIO(contents),
        key_prefix=f"employees/{emp.employee_code}/certificates",
        filename=name,
        content_type=mime,
    )
    cert = await exam_svc.admin_issue_certificate(
        db,
        payload={
            "employee_id": emp.id,
            "title": title[:200],
            "certificate_type": certificate_type,
            "body_text": (body_text or "").strip()[:1000] or None,
            "issued_date": issued_date,
            "file_key": key,
            "file_name": name[:255],
            "mime_type": mime,
        },
    )
    if emp.user_id:
        from app.services.notification_service import notify

        await notify(
            db,
            user_id=emp.user_id,
            type="certificate_issued",
            title=f"New certificate: {cert.title}",
            body="Download it from More → Certificates in the app.",
            data={"certificate_id": cert.id},
        )
    return cert


@router.put("/certificates/{certificate_id}", response_model=CertificateOut)
async def update_certificate(
    certificate_id: int,
    payload: CertificateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await exam_svc.update_certificate(
        db, certificate_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.post(
    "/certificates/{certificate_id}/revoke", response_model=CertificateOut
)
async def revoke_certificate(
    certificate_id: int,
    payload: CertificateRevoke,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await exam_svc.revoke_certificate(
        db, certificate_id, reason=payload.reason
    )


@router.post(
    "/certificates/{certificate_id}/restore", response_model=CertificateOut
)
async def restore_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await exam_svc.restore_certificate(db, certificate_id)


@router.get("/{exam_id}", response_model=ExamOut)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await exam_svc.get_exam(db, exam_id)


@router.post("/{exam_id}/publish", response_model=ExamOut)
async def publish_exam(
    exam_id: int,
    payload: ExamPublishUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await exam_svc.publish_exam(
        db, exam_id, is_published=payload.is_published
    )


@router.put("/{exam_id}", response_model=ExamOut)
async def update_exam(
    exam_id: int,
    payload: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    return await exam_svc.update_exam(
        db, exam_id, payload=payload.model_dump(exclude_unset=True)
    )


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    await exam_svc.delete_exam(db, exam_id)


@router.post("/{exam_id}/questions/bulk", response_model=ExamOut)
async def set_exam_questions_endpoint(
    exam_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    """Replace the question set on an exam in one shot.
    Body: {"question_ids": [1, 2, 3, ...]}"""
    ids = body.get("question_ids") or []
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        from fastapi import HTTPException
        raise HTTPException(400, detail="question_ids must be a list of ints")
    await exam_svc.set_exam_questions(db, exam_id, question_ids=ids)
    return await exam_svc.get_exam(db, exam_id)


# ─── Attempts ────────────────────────────────────────────────────────
def _public_question(q) -> QuestionPublic:
    return QuestionPublic(
        id=q.id,
        question_text=q.question_text,
        question_type=q.question_type,
        marks=q.marks,
        time_seconds=q.time_seconds,
        options=[
            {
                "id": o.id,
                "option_text": o.option_text,
                "sort_order": o.sort_order,
            }
            for o in q.options
        ],
    )


@router.post("/{exam_id}/start", response_model=StartAttemptResponse)
async def start_exam(
    exam_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exam = await exam_svc.get_exam(db, exam_id)
    emp = await _self_employee(db, user)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    attempt, questions = await exam_svc.start_attempt(
        db, exam=exam, employee=emp, ip_address=ip, device_info=ua
    )
    # Optionally shuffle each question's options
    publics = []
    for q in questions:
        if exam.shuffle_options:
            opts = list(q.options)
            import random as _r

            _r.shuffle(opts)
            q_public = QuestionPublic(
                id=q.id,
                question_text=q.question_text,
                question_type=q.question_type,
                marks=q.marks,
                time_seconds=q.time_seconds,
                options=[
                    {
                        "id": o.id,
                        "option_text": o.option_text,
                        "sort_order": i,
                    }
                    for i, o in enumerate(opts)
                ],
            )
        else:
            q_public = _public_question(q)
        publics.append(q_public)
    return StartAttemptResponse(
        attempt_id=attempt.id,
        started_at=attempt.started_at,
        time_limit_minutes=exam.time_limit_minutes,
        questions=publics,
    )


@router.post("/attempts/{attempt_id}/flag")
async def flag_attempt(
    attempt_id: int,
    payload: FlagSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attempt = await exam_svc.get_attempt(db, attempt_id)
    emp = await _self_employee(db, user)
    a = await exam_svc.add_cheating_flag(
        db,
        attempt=attempt,
        employee=emp,
        flag_type=payload.flag_type,
        note=payload.note,
    )
    return {
        "ok": True,
        "status": a.status,
        "flag_count": len(a.cheating_flags or []),
    }


@router.post(
    "/attempts/{attempt_id}/submit", response_model=AttemptResult
)
async def submit_attempt(
    attempt_id: int,
    payload: AttemptSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attempt = await exam_svc.get_attempt(db, attempt_id)
    emp = await _self_employee(db, user)
    answers = [a.model_dump() for a in payload.answers]
    return await exam_svc.submit_attempt(
        db,
        attempt=attempt,
        employee=emp,
        answers=answers,
        cheating_flags=payload.cheating_flags,
    )


@router.get(
    "/attempts/{attempt_id}", response_model=AttemptDetail
)
async def get_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    a = await exam_svc.get_attempt(db, attempt_id)
    emp = await _self_employee(db, user)
    if a.employee_id != emp.id:
        # Allow HR/admins to view too
        from app.core.permissions import Role as RoleEnum

        if not (
            set(user.role_codes)
            & {
                RoleEnum.SUPER_ADMIN.value,
                RoleEnum.HR.value,
                RoleEnum.ADMIN.value,
                RoleEnum.DIRECTOR.value,
            }
        ):
            from app.core.exceptions import ForbiddenError

            raise ForbiddenError("Not your attempt")
    return a


@router.get("/me/attempts", response_model=list[AttemptResult])
async def my_attempts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await exam_svc.list_my_attempts(db, emp.id)


# ─── Certificates ────────────────────────────────────────────────────
@router.get("/me/certificates", response_model=list[CertificateOut])
async def my_certificates(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await exam_svc.list_my_certificates(db, emp.id)


@router.get(
    "/certificates/verify",
    response_model=CertificateVerifyResponse,
)
async def verify_certificate_query(
    number: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Query-param variant. Use this when the certificate number contains
    slashes (e.g. JKT/CERT/2026/XYZ) so encodeURIComponent doesn't break
    routing."""
    return await exam_svc.verify_certificate(db, number)


@router.get(
    "/certificates/verify/{certificate_number:path}",
    response_model=CertificateVerifyResponse,
)
async def verify_certificate(
    certificate_number: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await exam_svc.verify_certificate(db, certificate_number)


@router.get("/certificates/{certificate_id}/pdf")
async def get_certificate_pdf(
    certificate_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cert = await exam_svc.get_certificate(db, certificate_id)
    employee = (
        await db.execute(
            select(Employee).where(Employee.id == cert.employee_id)
        )
    ).scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee not found")
    stem = cert.certificate_number.replace("/", "-")
    if cert.file_key:
        # Uploaded certificate — serve the file HR uploaded.
        from app.services import storage

        try:
            data = storage.read_bytes(cert.file_key)
        except FileNotFoundError as exc:
            raise NotFoundError("The certificate file is missing") from exc
        ext = (cert.file_name or "").rsplit(".", 1)[-1].lower() if "." in (cert.file_name or "") else "pdf"
        return Response(
            content=data,
            media_type=cert.mime_type or "application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{stem}.{ext}"',
                "Cache-Control": "no-store",
            },
        )
    pdf = render_certificate(certificate=cert, employee=employee)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{stem}.pdf"'
        },
    )

"""Phase 19 launch endpoints — notifications, audit, resignations, bulk import."""
import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.dependencies import get_current_user, get_db
from sqlalchemy import select
from app.models import Resignation, User
from app.schemas.launch import (
    AssetClearanceOut,
    TeamExitOut,
    AdminSeparationCreate,
    AdminSeparationUpdate,
    AuditLogOut,
    BroadcastResult,
    BulkImportResult,
    DeviceTokenOut,
    DeviceTokenRegister,
    NotificationBroadcast,
    NotificationOut,
    ResignationCreate,
    ResignationDecision,
    ResignationNdcUpdate,
    ResignationOut,
    ResignationSettle,
    SeparationEmailRequest,
    UnreadCount,
)
from app.services import (
    audit_service,
    bulk_import_service,
    employee_service as emp_svc,
    notification_service,
    resignation_service,
)

router = APIRouter(tags=["launch"])


async def _with_asset_counts(db: AsyncSession, rows):
    """Attach how many company assets each exiting employee still holds."""
    from app.services.asset_clearance import held_counts

    rows = list(rows)
    counts = await held_counts(db, [r.employee_id for r in rows])
    for r in rows:
        r.assets_pending_count = counts.get(r.employee_id, 0)
    return rows


async def _asset_clearance_out(db: AsyncSession, res: Resignation) -> dict:
    from app.services.asset_clearance import clearance

    data = await clearance(db, res.employee_id, since=res.requested_at)
    return {
        "resignation_id": res.id,
        "last_working_day": res.actual_last_working_day
        or res.proposed_last_working_day,
        **data,
    }


async def _self_employee(db: AsyncSession, user: User):
    emp = await emp_svc.get_self_employee(db, user)
    if not emp:
        raise NotFoundError("No employee record linked to this account")
    return emp


# ─── Notifications ───────────────────────────────────────────────────
@router.get(
    "/notifications/me",
    response_model=list[NotificationOut],
    tags=["notifications"],
)
async def my_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await notification_service.list_for_user(
        db, user_id=user.id, unread_only=unread_only
    )


@router.get(
    "/notifications/me/unread-count",
    response_model=UnreadCount,
    tags=["notifications"],
)
async def my_unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    n = await notification_service.unread_count(db, user_id=user.id)
    return UnreadCount(unread=n)


@router.post(
    "/notifications/{notification_id}/read",
    response_model=NotificationOut,
    tags=["notifications"],
)
async def read_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await notification_service.mark_read(
        db, notification_id, user_id=user.id
    )


@router.post("/notifications/me/read-all", tags=["notifications"])
async def read_all_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    n = await notification_service.mark_all_read(db, user_id=user.id)
    return {"marked": n}


@router.post(
    "/notifications/broadcast",
    response_model=BroadcastResult,
    tags=["notifications"],
)
async def broadcast_notification(
    payload: NotificationBroadcast,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.users.manage")),
):
    """Admin-initiated fan-out. audience can be all / role / department /
    users. send_push=True (default) also fires FCM to active device
    tokens for each recipient."""
    return await notification_service.broadcast(
        db,
        audience=payload.audience,
        title=payload.title,
        body=payload.body,
        type=payload.type,
        data=payload.data,
        send_push=payload.send_push,
        user_ids=payload.user_ids,
        role_codes=payload.role_codes,
        department_id=payload.department_id,
    )


@router.get(
    "/notifications/me/stream",
    tags=["notifications"],
    summary="SSE stream of unread-count updates (long-lived connection)",
)
async def stream_unread_count(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Long-lived Server-Sent Events stream that emits an
    `event: unread` message whenever the unread count changes, and a
    keepalive comment every 5s to defeat proxy timeouts. Reconnect with
    native EventSource semantics if the stream drops."""

    async def _gen() -> AsyncGenerator[str, None]:
        last = -1
        yield "event: hello\ndata: {}\n\n"
        while True:
            if await request.is_disconnected():
                return
            try:
                count = await notification_service.unread_count(
                    db, user_id=user.id
                )
            except Exception:
                count = last
            if count != last:
                yield f"event: unread\ndata: {json.dumps({'unread': count})}\n\n"
                last = count
            else:
                yield ": keepalive\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/notifications/devices",
    response_model=DeviceTokenOut,
    status_code=status.HTTP_201_CREATED,
    tags=["notifications"],
)
async def register_device(
    payload: DeviceTokenRegister,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await notification_service.register_device_token(
        db,
        user_id=user.id,
        platform=payload.platform,
        token=payload.token,
    )


@router.delete(
    "/notifications/devices/{token}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["notifications"],
)
async def unregister_device(
    token: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    await notification_service.unregister_device_token(
        db, token=token, user_id=user.id
    )


# ─── Audit ───────────────────────────────────────────────────────────
@router.get(
    "/audit",
    response_model=list[AuditLogOut],
    tags=["audit"],
)
async def list_audit(
    actor_user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    since_days: Optional[int] = Query(default=30, ge=1, le=730),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.audit.view")),
):
    return await audit_service.list_logs(
        db,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        since_days=since_days,
        limit=limit,
    )


# ─── Resignations ────────────────────────────────────────────────────
@router.post(
    "/resignations",
    response_model=ResignationOut,
    status_code=status.HTTP_201_CREATED,
    tags=["resignations"],
)
async def submit_resignation(
    payload: ResignationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    res = await resignation_service.submit(
        db,
        employee=emp,
        proposed_last_working_day=payload.proposed_last_working_day,
        reason=payload.reason,
        notice_period_days=payload.notice_period_days,
    )

    # Notify the manager (if any)
    if emp.reporting_to:
        from sqlalchemy import select
        from app.models import Employee

        manager_emp = (
            await db.execute(
                select(Employee).where(Employee.id == emp.reporting_to)
            )
        ).scalar_one_or_none()
        if manager_emp and manager_emp.user_id:
            await notification_service.notify(
                db,
                user_id=manager_emp.user_id,
                type="resignation.submitted",
                title="A direct report has resigned",
                body=(
                    f"{emp.first_name} {emp.last_name} ({emp.employee_code}) "
                    f"submitted a resignation effective "
                    f"{payload.proposed_last_working_day}."
                ),
                data={"resignation_id": res.id, "employee_id": emp.id},
                send_email_now=True,
                email_template="resignation_submitted",
                email_params={
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "employee_code": emp.employee_code,
                    "last_day": str(payload.proposed_last_working_day),
                    "reason": payload.reason or "—",
                },
            )
    return res


@router.get(
    "/resignations/me",
    response_model=list[ResignationOut],
    tags=["resignations"],
)
async def my_resignations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await _with_asset_counts(
        db, await resignation_service.list_for_employee(db, emp.id)
    )


@router.get(
    "/resignations/team",
    response_model=list[TeamExitOut],
    tags=["resignations"],
)
async def team_exits(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """For a reporting manager: direct reports who are leaving, with
    their asset return (NOC) status."""
    from app.models import Employee
    from app.services.asset_clearance import OPEN_EXIT_STATES

    me = await emp_svc.get_self_employee(db, user)
    if me is None:
        return []
    rows = (
        await db.execute(
            select(Resignation, Employee)
            .join(Employee, Employee.id == Resignation.employee_id)
            .where(Employee.reporting_to == me.id)
            .where(Resignation.status.in_(OPEN_EXIT_STATES))
            .order_by(Resignation.proposed_last_working_day)
        )
    ).all()
    out = []
    for res, emp in rows:
        assets = await _asset_clearance_out(db, res)
        res.assets_pending_count = assets["pending_count"]
        out.append(
            {
                "resignation": res,
                "employee": {
                    "id": emp.id,
                    "employee_code": emp.employee_code,
                    "name": f"{emp.first_name} {emp.last_name}".strip(),
                    "designation": emp.designation.name if emp.designation else None,
                    "photo_url": emp.photo_url,
                },
                "assets": assets,
            }
        )
    return out


@router.get(
    "/resignations/{resignation_id}/assets",
    response_model=AssetClearanceOut,
    tags=["resignations"],
)
async def resignation_assets(
    resignation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Asset NOC for one exit. Visible to HR (approval.act), the
    employee, and their direct reporting manager."""
    from app.core.exceptions import ForbiddenError
    from app.models import Employee

    res = await resignation_service.get(db, resignation_id)
    codes = user.permission_codes
    if "approval.act" not in codes and "system.config" not in codes:
        me = await emp_svc.get_self_employee(db, user)
        target = (
            await db.execute(select(Employee).where(Employee.id == res.employee_id))
        ).scalar_one_or_none()
        allowed = me is not None and target is not None and (
            target.id == me.id or target.reporting_to == me.id
        )
        if not allowed:
            raise ForbiddenError("Not allowed to view this exit")
    return await _asset_clearance_out(db, res)


@router.get(
    "/resignations/me/unlock-status",
    tags=["resignations"],
)
async def my_unlock_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mobile-side check: is the current employee allowed to submit a
    resignation right now?"""
    emp = await _self_employee(db, user)
    has_open = (
        await db.execute(
            select(Resignation)
            .where(Resignation.employee_id == emp.id)
            .where(
                Resignation.status.notin_(
                    ["rejected", "settled", "cancelled"]
                )
            )
        )
    ).scalar_one_or_none()
    return {
        "unlocked": bool(getattr(emp, "resignation_unlocked", False)),
        "has_open_request": has_open is not None,
    }


@router.post(
    "/resignations/employees/{employee_id}/unlock",
    tags=["resignations"],
)
async def admin_set_resignation_unlock(
    employee_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    """Admin-only switch. Pass {"unlocked": true|false}. The flag also
    auto-resets to false right after the employee submits, so this is
    a one-shot per request."""
    from app.services import employee_service as emp_svc

    emp = await emp_svc.get_employee(db, employee_id)
    unlocked = bool(payload.get("unlocked", True))
    emp = await resignation_service.set_resignation_unlock(
        db, employee=emp, unlocked=unlocked
    )
    return {
        "employee_id": emp.id,
        "resignation_unlocked": emp.resignation_unlocked,
    }


@router.get(
    "/resignations/pending",
    response_model=list[ResignationOut],
    tags=["resignations"],
)
async def pending_resignations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await _with_asset_counts(db, await resignation_service.list_pending(db))


@router.get(
    "/resignations",
    response_model=list[ResignationOut],
    tags=["resignations"],
)
async def list_resignations(
    resignation_status: Optional[str] = Query(default=None, alias="status"),
    employee_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await _with_asset_counts(
        db,
        await resignation_service.list_resignations(
            db,
            status=resignation_status,
            employee_id=employee_id,
            search=search,
        ),
    )


_RESIGNATION_DOC_KINDS = {
    "resignation_letter",
    "noc",
    "experience_letter",
    "settlement_sheet",
    "asset_handover",
    "other",
}
_RESIGNATION_DOC_MIME = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/zip",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@router.post(
    "/resignations/{resignation_id}/documents",
    response_model=ResignationOut,
    tags=["resignations"],
)
async def upload_resignation_document(
    resignation_id: int,
    file: UploadFile = File(...),
    kind: str = Form("other"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    """Attach a PDF / image / spreadsheet to a resignation. Kinds:
    resignation_letter, noc, experience_letter, settlement_sheet,
    asset_handover, other."""
    from app.core.exceptions import ValidationError
    from app.services.storage import upload_fileobj

    if kind not in _RESIGNATION_DOC_KINDS:
        raise ValidationError(f"kind must be one of: {sorted(_RESIGNATION_DOC_KINDS)}")
    if file.content_type and file.content_type.lower() not in _RESIGNATION_DOC_MIME:
        raise ValidationError(f"Unsupported content type: {file.content_type}")
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise ValidationError("File too large (max 25 MB)")

    import io
    _, url = upload_fileobj(
        io.BytesIO(contents),
        key_prefix=f"resignations/{resignation_id}/{kind}",
        filename=file.filename or f"{kind}.bin",
        content_type=file.content_type,
    )
    return await resignation_service.attach_document(
        db,
        resignation_id,
        url=url,
        name=file.filename or f"{kind}.bin",
        mime=file.content_type,
        size=len(contents),
        kind=kind,
        uploaded_by=user.id,
    )


@router.delete(
    "/resignations/{resignation_id}/documents/{doc_index}",
    response_model=ResignationOut,
    tags=["resignations"],
)
async def remove_resignation_document(
    resignation_id: int,
    doc_index: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await resignation_service.remove_document(
        db, resignation_id, index=doc_index
    )


@router.post(
    "/resignations/{resignation_id}/decision",
    response_model=ResignationOut,
    tags=["resignations"],
)
async def decide_resignation(
    resignation_id: int,
    payload: ResignationDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # HR / admin accounts often have no linked Employee row, so we
    # look one up when the caller has it (needed for the reporting-
    # manager check) but pass ``None`` through otherwise — the service
    # falls back to the role-based bypass.
    manager_emp = await emp_svc.get_self_employee(db, user)
    return await resignation_service.manager_decision(
        db,
        resignation_id,
        manager=user,
        manager_employee=manager_emp,
        accept=payload.accept,
        comment=payload.comment,
        actual_last_working_day=payload.actual_last_working_day,
    )


@router.patch(
    "/resignations/{resignation_id}/ndc",
    response_model=ResignationOut,
    tags=["resignations"],
)
async def update_resignation_ndc(
    resignation_id: int,
    payload: ResignationNdcUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("approval.act")),
):
    return await resignation_service.update_ndc(
        db, resignation_id, actor=user, updates=payload.updates
    )


@router.post(
    "/resignations/{resignation_id}/settle",
    response_model=ResignationOut,
    tags=["resignations"],
)
async def settle_resignation(
    resignation_id: int,
    payload: ResignationSettle,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("payroll.run")),
):
    return await resignation_service.settle(
        db,
        resignation_id,
        actor=user,
        final_settlement_amount=payload.final_settlement_amount,
        exit_interview_notes=payload.exit_interview_notes,
    )


@router.post(
    "/resignations/{resignation_id}/cancel",
    response_model=ResignationOut,
    tags=["resignations"],
)
async def cancel_resignation(
    resignation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = await _self_employee(db, user)
    return await resignation_service.cancel(db, resignation_id, employee=emp)


# ─── Bulk import ─────────────────────────────────────────────────────
@router.post(
    "/employees/bulk-import",
    response_model=BulkImportResult,
    tags=["employees"],
)
async def bulk_import_employees(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.create")),
):
    contents = await file.read()
    return await bulk_import_service.import_employees_csv(
        db, csv_bytes=contents
    )


# ─── Admin-initiated separation (resign / terminate on behalf) ─────────
@router.post(
    "/separations",
    response_model=ResignationOut,
    status_code=status.HTTP_201_CREATED,
    tags=["separations"],
)
async def admin_create_separation(
    payload: AdminSeparationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("employee.update")),
):
    from app.models import Employee
    from app.services import employee_service as emp_svc

    emp = await emp_svc.get_employee(db, payload.employee_id)
    res = await resignation_service.admin_initiate(
        db,
        employee=emp,
        separation_type=payload.separation_type,
        proposed_last_working_day=payload.proposed_last_working_day,
        reason=payload.reason,
        notice_period_days=payload.notice_period_days,
        manager_comment=payload.manager_comment,
        actor=user,
    )
    # Best-effort in-app notification for the employee.
    if emp.user_id:
        try:
            await notification_service.notify(
                db,
                user_id=emp.user_id,
                type="separation.initiated",
                title=(
                    "Termination notice issued"
                    if payload.separation_type == "termination"
                    else "Resignation processed"
                ),
                body=(
                    f"Your last working day is "
                    f"{payload.proposed_last_working_day.strftime('%d %b %Y')}."
                ),
                data={"resignation_id": res.id, "type": payload.separation_type},
            )
        except Exception:
            pass
    return res


@router.get(
    "/separations/{resignation_id}/pdf",
    tags=["separations"],
)
async def download_separation_pdf(
    resignation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    from fastapi import Response
    from app.services import employee_service as emp_svc

    res = await resignation_service.get(db, resignation_id)
    emp = await emp_svc.get_employee(db, res.employee_id)
    pdf = resignation_service.render_separation_pdf(res, emp)
    kind = (
        "termination" if getattr(res, "separation_type", "resignation") == "termination"
        else "resignation"
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{kind}_{emp.employee_code}.pdf"'
            ),
            "Cache-Control": "no-store",
        },
    )


@router.post(
    "/separations/{resignation_id}/email",
    tags=["separations"],
)
async def email_separation_letter(
    resignation_id: int,
    payload: SeparationEmailRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    from app.services import employee_service as emp_svc
    from app.services.email_service import send_email

    res = await resignation_service.get(db, resignation_id)
    emp = await emp_svc.get_employee(db, res.employee_id)
    pdf = resignation_service.render_separation_pdf(res, emp)

    to_email = (payload.to or emp.personal_email or "").strip()
    if not to_email:
        raise NotFoundError(
            "No email address on record for this employee — pass `to` "
            "to override."
        )
    kind = (
        "termination" if getattr(res, "separation_type", "resignation") == "termination"
        else "resignation"
    )
    subject = payload.subject or (
        f"Notice of Termination — {emp.first_name} {emp.last_name}"
        if kind == "termination"
        else f"Acceptance of Resignation — {emp.first_name} {emp.last_name}"
    )
    body_html = payload.body or (
        f"<p>Dear {emp.first_name},</p>"
        f"<p>Please find attached the formal letter regarding your "
        f"{'termination' if kind == 'termination' else 'resignation'} "
        f"from Jaikalki Technology Pvt Ltd.</p>"
        f"<p>Regards,<br/>Human Resources</p>"
    )
    ok, err = await send_email(
        to_email=to_email,
        to_name=f"{emp.first_name} {emp.last_name}",
        subject=subject,
        html=body_html,
        cc=payload.cc,
        attachments=[
            {
                "filename": f"{kind}_{emp.employee_code}.pdf",
                "content": pdf,
                "mime": "application/pdf",
            }
        ],
    )
    if not ok:
        from app.core.exceptions import ValidationError as _V
        raise _V(f"Could not send email: {err}")
    return {"sent": True, "to": to_email, "cc": payload.cc or []}


@router.patch(
    "/separations/{resignation_id}",
    response_model=ResignationOut,
    tags=["separations"],
)
async def admin_update_separation(
    resignation_id: int,
    payload: AdminSeparationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    return await resignation_service.admin_update(
        db, resignation_id, fields=payload.model_dump(exclude_unset=True)
    )


@router.post("/separations/{resignation_id}/undo", tags=["separations"])
async def admin_undo_separation(
    resignation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    return await resignation_service.admin_undo(db, resignation_id)


@router.delete(
    "/separations/{resignation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["separations"],
)
async def admin_delete_separation(
    resignation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("employee.update")),
):
    await resignation_service.admin_delete(db, resignation_id)

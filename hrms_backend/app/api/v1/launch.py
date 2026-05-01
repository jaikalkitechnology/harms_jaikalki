"""Phase 19 launch endpoints — notifications, audit, resignations, bulk import."""
import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
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
from app.models import User
from app.schemas.launch import (
    AuditLogOut,
    BulkImportResult,
    DeviceTokenOut,
    DeviceTokenRegister,
    NotificationOut,
    ResignationCreate,
    ResignationDecision,
    ResignationNdcUpdate,
    ResignationOut,
    ResignationSettle,
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
    return await resignation_service.list_for_employee(db, emp.id)


@router.get(
    "/resignations/pending",
    response_model=list[ResignationOut],
    tags=["resignations"],
)
async def pending_resignations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("approval.act")),
):
    return await resignation_service.list_pending(db)


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
    manager_emp = await _self_employee(db, user)
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

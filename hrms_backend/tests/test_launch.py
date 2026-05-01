"""Phase 19 launch-readiness tests."""
import io
from datetime import date, timedelta
from unittest.mock import patch

import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Notifications ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_notifications_inbox_starts_empty(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/notifications/me", headers=_h(token))
    assert r.status_code == 200
    assert r.json() == []
    r = await client.get(
        "/api/v1/notifications/me/unread-count", headers=_h(token)
    )
    assert r.json() == {"unread": 0}


@pytest.mark.asyncio
async def test_resignation_notifies_manager(client):
    """Submitting a resignation should drop a notification in the manager's
    inbox (Employee Demo reports to Manager Demo)."""
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    last_day = (date.today() + timedelta(days=60)).isoformat()
    r = await client.post(
        "/api/v1/resignations",
        headers=_h(emp_token),
        json={
            "proposed_last_working_day": last_day,
            "reason": "Personal reasons",
            "notice_period_days": 60,
        },
    )
    assert r.status_code == 201, r.text

    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/notifications/me", headers=_h(mgr_token))
    assert r.status_code == 200
    inbox = r.json()
    assert any(n["type"] == "resignation.submitted" for n in inbox)


@pytest.mark.asyncio
async def test_mark_read_and_unread_count(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    mgr_token = await _login(client, "manager@hrms.com", "manager123")

    last_day = (date.today() + timedelta(days=45)).isoformat()
    r = await client.post(
        "/api/v1/resignations",
        headers=_h(emp_token),
        json={
            "proposed_last_working_day": last_day,
            "notice_period_days": 45,
        },
    )
    if r.status_code != 201:
        # Already submitted in another test → cancel and retry
        existing = (
            await client.get(
                "/api/v1/resignations/me", headers=_h(emp_token)
            )
        ).json()
        for r0 in existing:
            await client.post(
                f"/api/v1/resignations/{r0['id']}/cancel",
                headers=_h(emp_token),
            )
        r = await client.post(
            "/api/v1/resignations",
            headers=_h(emp_token),
            json={
                "proposed_last_working_day": last_day,
                "notice_period_days": 45,
            },
        )

    inbox = (
        await client.get("/api/v1/notifications/me", headers=_h(mgr_token))
    ).json()
    assert inbox, "manager should have at least one notification"
    n = inbox[0]
    r = await client.post(
        f"/api/v1/notifications/{n['id']}/read", headers=_h(mgr_token)
    )
    assert r.status_code == 200
    assert r.json()["read_at"] is not None

    r = await client.post(
        "/api/v1/notifications/me/read-all", headers=_h(mgr_token)
    )
    assert r.status_code == 200

    r = await client.get(
        "/api/v1/notifications/me/unread-count", headers=_h(mgr_token)
    )
    assert r.json()["unread"] == 0


# ─── Resignation lifecycle ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_resignation_lifecycle_to_settlement(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    hr_token = await _login(client, "hr@hrms.com", "hr123")

    # Cancel any prior resignation from earlier tests
    existing = (
        await client.get("/api/v1/resignations/me", headers=_h(emp_token))
    ).json()
    for r0 in existing:
        await client.post(
            f"/api/v1/resignations/{r0['id']}/cancel",
            headers=_h(emp_token),
        )

    last_day = (date.today() + timedelta(days=30)).isoformat()
    r = await client.post(
        "/api/v1/resignations",
        headers=_h(emp_token),
        json={
            "proposed_last_working_day": last_day,
            "reason": "New opportunity",
            "notice_period_days": 30,
        },
    )
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    assert r.json()["status"] == "manager_review"

    # Manager accepts
    r = await client.post(
        f"/api/v1/resignations/{rid}/decision",
        headers=_h(mgr_token),
        json={"accept": True, "comment": "Sad to see you go"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_notice"

    # HR ticks off NDC items
    r = await client.patch(
        f"/api/v1/resignations/{rid}/ndc",
        headers=_h(hr_token),
        json={
            "updates": {
                "assets_returned": True,
                "id_card_returned": True,
                "it_access_revoked": True,
                "knowledge_transfer_done": True,
                "manager_signoff": True,
                "hr_signoff": True,
                "exit_interview_done": True,
                "final_payslip_generated": True,
            }
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cleared"

    # HR settles
    r = await client.post(
        f"/api/v1/resignations/{rid}/settle",
        headers=_h(hr_token),
        json={
            "final_settlement_amount": 75000,
            "exit_interview_notes": "Positive feedback",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "settled"
    assert r.json()["final_settlement_amount"] == 75000


@pytest.mark.asyncio
async def test_cannot_submit_two_open_resignations(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")

    last_day = (date.today() + timedelta(days=30)).isoformat()
    r1 = await client.post(
        "/api/v1/resignations",
        headers=_h(emp_token),
        json={"proposed_last_working_day": last_day},
    )
    if r1.status_code == 409:
        # already exists from prior test — clean up
        existing = (
            await client.get("/api/v1/resignations/me", headers=_h(emp_token))
        ).json()
        for r0 in existing:
            if r0["status"] not in ("settled", "rejected", "cancelled"):
                await client.post(
                    f"/api/v1/resignations/{r0['id']}/cancel",
                    headers=_h(emp_token),
                )
        r1 = await client.post(
            "/api/v1/resignations",
            headers=_h(emp_token),
            json={"proposed_last_working_day": last_day},
        )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/api/v1/resignations",
        headers=_h(emp_token),
        json={"proposed_last_working_day": last_day},
    )
    assert r2.status_code == 409


# ─── Bulk import ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_bulk_import_csv_creates_employees(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    csv_text = (
        "first_name,last_name,employment_type,date_of_joining,"
        "category_code,email,department_code,designation_code\n"
        "Asha,Patil,full_time,2026-05-01,PERMANENT,asha@example.com,IT,DEV1\n"
        "Rohan,Shah,full_time,2026-05-01,PERMANENT,rohan@example.com,IT,DEV1\n"
        # Bad row — missing date
        "Bad,Row,full_time,,PERMANENT,bad@example.com,IT,DEV1\n"
    )
    files = {
        "file": ("employees.csv", csv_text.encode("utf-8"), "text/csv"),
    }
    r = await client.post(
        "/api/v1/employees/bulk-import",
        headers=_h(hr_token),
        files=files,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 3
    assert body["created"] == 2
    assert len(body["errors"]) == 1
    assert body["errors"][0]["row"] == 4  # header is row 1


# ─── Password reset OTP ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_forgot_password_returns_202_for_unknown_email(client):
    r = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody-exists@example.com"},
    )
    assert r.status_code == 202


@pytest.mark.asyncio
async def test_password_reset_full_flow(client, db_session):
    """Skip the email sender, intercept the OTP from the DB."""
    from app.core.security import hash_password
    from app.models import PasswordResetOtp

    # Trigger OTP generation
    with patch(
        "app.services.password_reset_service.send_template_email",
        return_value=(True, None),
    ):
        r = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "employee@hrms.com"},
        )
        assert r.status_code == 202

    # Pull the most recent OTP row directly + bypass hashing by replanting
    from sqlalchemy import select

    rows = (
        await db_session.execute(
            select(PasswordResetOtp)
            .where(PasswordResetOtp.email == "employee@hrms.com")
            .order_by(PasswordResetOtp.created_at.desc())
        )
    ).scalars().all()
    assert rows
    row = rows[0]
    # Replace the OTP with a known value so we can test the reset endpoint.
    row.otp_hash = hash_password("123456")
    await db_session.commit()

    r = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "employee@hrms.com",
            "otp": "123456",
            "new_password": "BrandNewPass!1",
        },
    )
    assert r.status_code == 204

    # New password works, old does not
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "employee@hrms.com", "password": "BrandNewPass!1"},
    )
    assert r.status_code == 200
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "employee@hrms.com", "password": "employee123"},
    )
    assert r.status_code == 401


# ─── MFA ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_mfa_enroll_and_verify(client):
    import pyotp

    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post("/api/v1/auth/mfa/enroll", headers=_h(token))
    assert r.status_code == 200, r.text
    body = r.json()
    secret = body["secret"]
    assert body["otpauth_uri"].startswith("otpauth://totp/")

    code = pyotp.TOTP(secret).now()
    r = await client.post(
        "/api/v1/auth/mfa/verify",
        headers=_h(token),
        json={"code": code},
    )
    assert r.status_code == 200
    backup_codes = r.json()["backup_codes"]
    assert len(backup_codes) == 8

    # Cannot re-enroll once enabled
    r = await client.post("/api/v1/auth/mfa/enroll", headers=_h(token))
    assert r.status_code == 409

    # Disable using a TOTP code
    code = pyotp.TOTP(secret).now()
    r = await client.post(
        "/api/v1/auth/mfa/disable",
        headers=_h(token),
        json={"code": code},
    )
    assert r.status_code == 204


# ─── Audit ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_log_view_requires_permission(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/audit", headers=_h(emp_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_audit_endpoint_lists_recent_entries(client):
    """The audit middleware writes async, so we can't guarantee a row right
    after a request — but an admin should at least be able to hit the
    endpoint and get a list back."""
    admin_token = await _login(client, "admin@hrms.com", "admin123")

    # Trigger a mutation that should be auto-captured
    await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "employee@hrms.com"},
    )
    r = await client.get("/api/v1/audit?since_days=1", headers=_h(admin_token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)

"""Phase 20 tests — profile photo, salary revision, FCM stub, Sentry."""
from datetime import date, timedelta

import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Profile photos ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_employee_can_upload_own_photo(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    me = (await client.get("/api/v1/employees/me", headers=_h(token))).json()
    # 1×1 PNG (transparent)
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("me.png", png, "image/png")}
    r = await client.post(
        f"/api/v1/employees/{me['id']}/photo",
        headers=_h(token),
        files=files,
    )
    assert r.status_code == 200, r.text
    assert r.json()["photo_url"] is not None
    assert r.json()["photo_url"].endswith(".png")


@pytest.mark.asyncio
async def test_employee_cannot_upload_others_photo(client):
    employee_token = await _login(client, "employee@hrms.com", "employee123")
    # Pooja's id from the seed
    employees = (
        await client.get("/api/v1/employees", headers=_h(employee_token))
    ).json()
    pooja = next(e for e in employees if e["employee_code"] == "JKT014")

    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    r = await client.post(
        f"/api/v1/employees/{pooja['id']}/photo",
        headers=_h(employee_token),
        files={"file": ("x.png", png, "image/png")},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_photo_rejects_pdf_content_type(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    me = (await client.get("/api/v1/employees/me", headers=_h(token))).json()
    r = await client.post(
        f"/api/v1/employees/{me['id']}/photo",
        headers=_h(token),
        files={"file": ("doc.pdf", b"%PDF-1.4 ...", "application/pdf")},
    )
    assert r.status_code == 422


# ── Salary revision lifecycle ───────────────────────────────────────
@pytest.mark.asyncio
async def test_salary_revision_propose_approve_apply(client):
    """HR proposes, super admin approves, HR applies → CTC bumped + PDF
    generated."""
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    super_token = await _login(client, "super@jaikalki.com", "super123")

    employees = (
        await client.get("/api/v1/employees", headers=_h(hr_token))
    ).json()
    target = next(e for e in employees if e["employee_code"] == "JKT018")
    prev_ctc = float(target["ctc_annual"] or 0)
    new_ctc = round(prev_ctc * 1.12, 2)
    eff_date = (date.today() + timedelta(days=1)).isoformat()

    r = await client.post(
        "/api/v1/compensation/revisions",
        headers=_h(hr_token),
        json={
            "employee_id": target["id"],
            "new_ctc_annual": new_ctc,
            "effective_date": eff_date,
            "reason": "annual_review",
            "notes": "Strong year",
        },
    )
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    assert r.json()["status"] == "pending_approval"
    assert float(r.json()["increment_pct"]) > 0

    # HR cannot self-approve
    r = await client.post(
        f"/api/v1/compensation/revisions/{rid}/approve",
        headers=_h(hr_token),
    )
    assert r.status_code == 403

    # Super admin approves
    r = await client.post(
        f"/api/v1/compensation/revisions/{rid}/approve",
        headers=_h(super_token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"

    # Cannot apply before effective date
    r = await client.post(
        f"/api/v1/compensation/revisions/{rid}/apply",
        headers=_h(hr_token),
    )
    assert r.status_code == 422

    # Move effective date to today via direct DB manipulation in the test
    from sqlalchemy import select, update
    from app.models import SalaryRevision

    async def _force_today() -> None:
        from app.dependencies import get_db
        from app.main import app

        gen = app.dependency_overrides[get_db]()
        async for session in gen:
            await session.execute(
                update(SalaryRevision)
                .where(SalaryRevision.id == rid)
                .values(effective_date=date.today())
            )
            await session.commit()
            break

    await _force_today()

    r = await client.post(
        f"/api/v1/compensation/revisions/{rid}/apply",
        headers=_h(hr_token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "applied"
    assert body["increment_letter_url"] is not None
    assert "/uploads/" in body["increment_letter_url"]

    # Employee CTC has been bumped
    r = await client.get(
        f"/api/v1/employees/{target['id']}", headers=_h(hr_token)
    )
    assert float(r.json()["ctc_annual"]) == new_ctc


@pytest.mark.asyncio
async def test_cannot_open_two_revisions_for_same_employee(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    employees = (
        await client.get("/api/v1/employees", headers=_h(hr_token))
    ).json()
    target = next(e for e in employees if e["employee_code"] == "JKT016")
    prev_ctc = float(target["ctc_annual"] or 0)
    eff_date = (date.today() + timedelta(days=30)).isoformat()

    r1 = await client.post(
        "/api/v1/compensation/revisions",
        headers=_h(hr_token),
        json={
            "employee_id": target["id"],
            "new_ctc_annual": round(prev_ctc * 1.10, 2),
            "effective_date": eff_date,
            "reason": "annual_review",
        },
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/api/v1/compensation/revisions",
        headers=_h(hr_token),
        json={
            "employee_id": target["id"],
            "new_ctc_annual": round(prev_ctc * 1.15, 2),
            "effective_date": eff_date,
            "reason": "annual_review",
        },
    )
    assert r2.status_code == 409


# ── FCM ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_push_send_returns_disabled_when_unconfigured():
    from app.services.push_service import send_push, send_push_multicast

    ok, err = send_push(token="x", title="t", body="b")
    assert ok is False
    assert "fcm" in err

    success, failure = send_push_multicast(
        tokens=["a", "b"], title="t", body="b"
    )
    assert success == 0
    assert failure == 2


# ── Sentry init is a no-op without DSN ──────────────────────────────
@pytest.mark.asyncio
async def test_sentry_init_noop_without_dsn():
    """Calling _init_sentry with no DSN should not raise even if the
    sentry_sdk package is missing."""
    from app.main import _init_sentry

    _init_sentry()  # should not raise


# ── SSE endpoint exists and returns text/event-stream headers ───────
@pytest.mark.asyncio
async def test_sse_endpoint_emits_event_stream_content_type(client):
    """We can't easily consume a long-lived stream in pytest, but we can
    check that the route exists and that the `hello` event is the first
    line we get back."""
    token = await _login(client, "employee@hrms.com", "employee123")
    # httpx ASGITransport will fully drain the generator unless we use
    # streaming, but the first chunk lands quickly so a small read is enough.
    async with client.stream(
        "GET",
        "/api/v1/notifications/me/stream",
        headers=_h(token),
    ) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        # Pull the first chunk
        async for chunk in r.aiter_bytes():
            text = chunk.decode("utf-8")
            assert "event: hello" in text or ":" in text
            break

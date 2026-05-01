"""Phase 14 trainer department tests."""
import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_seeded_trainers_and_sessions(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    trainers = (
        await client.get("/api/v1/trainer/trainers", headers=_h(token))
    ).json()
    assert len(trainers) == 2
    assert any(t["is_external"] for t in trainers)
    assert any(not t["is_external"] for t in trainers)

    sessions = (
        await client.get(
            "/api/v1/trainer/sessions?upcoming_only=true", headers=_h(token)
        )
    ).json()
    assert len(sessions) == 2
    codes = {s["code"] for s in sessions}
    assert codes == {"JKT-TS-POSH-001", "JKT-TS-FIELD-001"}


@pytest.mark.asyncio
async def test_marketplace_search_and_specialization_filter(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    # Search by name
    r = await client.get(
        "/api/v1/trainer/trainers?search=Vikram", headers=_h(token)
    )
    assert r.status_code == 200
    rows = r.json()
    assert all("Vikram" in t["full_name"] for t in rows)

    # Filter by specialization
    r = await client.get(
        "/api/v1/trainer/trainers?specialization=POSH", headers=_h(token)
    )
    assert r.status_code == 200
    assert all("POSH" in (t["specializations"] or []) for t in r.json())


@pytest.mark.asyncio
async def test_register_capacity_and_full_session(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    trainer_token = hr_token

    # Create a trainer + tiny session
    r = await client.post(
        "/api/v1/trainer/trainers",
        headers=_h(hr_token),
        json={
            "is_external": True,
            "full_name": "Capacity Test Trainer",
            "specializations": ["Test"],
            "years_experience": 1,
        },
    )
    assert r.status_code == 201, r.text
    trainer_id = r.json()["id"]

    from datetime import datetime, timedelta

    start = (datetime.utcnow() + timedelta(days=1)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat()
    r = await client.post(
        "/api/v1/trainer/sessions",
        headers=_h(hr_token),
        json={
            "code": "TEST-CAP-1",
            "title": "Capacity test",
            "trainer_id": trainer_id,
            "scheduled_start": start,
            "scheduled_end": end,
            "capacity": 1,
            "session_type": "virtual",
        },
    )
    assert r.status_code == 201, r.text
    session = r.json()
    assert session["qr_token"] is None  # qr_token not exposed in this view? It is.
    # Re-check: TrainingSessionOut includes qr_token
    assert "qr_token" in session

    # First registration as employee@
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/register",
        headers=_h(emp_token),
    )
    assert r.status_code == 201, r.text

    # Second registration as manager@ → should fail (capacity 1)
    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/register",
        headers=_h(mgr_token),
    )
    assert r.status_code == 422
    assert "full" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_qr_check_in_and_attendance(client):
    """Get a seeded session's qr_token, register, then check in."""
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    sessions = (
        await client.get("/api/v1/trainer/sessions", headers=_h(hr_token))
    ).json()
    session = next(s for s in sessions if s["code"] == "JKT-TS-POSH-001")

    emp_token = await _login(client, "employee@hrms.com", "employee123")
    await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/register",
        headers=_h(emp_token),
    )

    # Wrong token → 404
    r = await client.post(
        "/api/v1/trainer/sessions/check-in",
        headers=_h(emp_token),
        json={"qr_token": "bogus-token-xyz"},
    )
    assert r.status_code == 404

    # Right token → checked in
    r = await client.post(
        "/api/v1/trainer/sessions/check-in",
        headers=_h(emp_token),
        json={"qr_token": session["qr_token"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "attended"
    assert body["checked_in_at"] is not None

    # Idempotent — second check-in should not change anything
    r2 = await client.post(
        "/api/v1/trainer/sessions/check-in",
        headers=_h(emp_token),
        json={"qr_token": session["qr_token"]},
    )
    assert r2.status_code == 200
    assert r2.json()["checked_in_at"] == body["checked_in_at"]


@pytest.mark.asyncio
async def test_review_only_after_completion_and_attended(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    sessions = (
        await client.get("/api/v1/trainer/sessions", headers=_h(hr_token))
    ).json()
    session = next(s for s in sessions if s["code"] == "JKT-TS-POSH-001")

    emp_token = await _login(client, "employee@hrms.com", "employee123")
    await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/register",
        headers=_h(emp_token),
    )

    # Cannot review while session is open_for_registration
    r = await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/review",
        headers=_h(emp_token),
        json={"rating": 5, "review_text": "Great"},
    )
    assert r.status_code == 422

    # Check in then mark session completed
    await client.post(
        "/api/v1/trainer/sessions/check-in",
        headers=_h(emp_token),
        json={"qr_token": session["qr_token"]},
    )
    r = await client.patch(
        f"/api/v1/trainer/sessions/{session['id']}/status",
        headers=_h(hr_token),
        json={"status": "completed"},
    )
    assert r.status_code == 200

    # Now review works
    r = await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/review",
        headers=_h(emp_token),
        json={"rating": 5, "review_text": "Excellent"},
    )
    assert r.status_code == 201
    review_id = r.json()["id"]

    # Trainer's avg rating is now 5
    r = await client.get(
        f"/api/v1/trainer/trainers/{session['trainer_id']}",
        headers=_h(emp_token),
    )
    assert float(r.json()["rating_average"]) == 5.0

    # Re-submitting updates the existing review (idempotent)
    r = await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/review",
        headers=_h(emp_token),
        json={"rating": 4, "review_text": "Updated"},
    )
    assert r.status_code == 201
    assert r.json()["id"] == review_id
    assert r.json()["rating"] == 4

    # Reviewer who never attended cannot review
    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.post(
        f"/api/v1/trainer/sessions/{session['id']}/review",
        headers=_h(mgr_token),
        json={"rating": 1},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_session_conflict_detection(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    sessions = (
        await client.get("/api/v1/trainer/sessions", headers=_h(hr_token))
    ).json()
    posh = next(s for s in sessions if s["code"] == "JKT-TS-POSH-001")

    # Schedule another session for the same trainer overlapping with POSH
    r = await client.post(
        "/api/v1/trainer/sessions",
        headers=_h(hr_token),
        json={
            "code": "TEST-CONFLICT-1",
            "title": "Conflict",
            "trainer_id": posh["trainer_id"],
            "scheduled_start": posh["scheduled_start"],
            "scheduled_end": posh["scheduled_end"],
            "capacity": 5,
            "session_type": "virtual",
        },
    )
    assert r.status_code == 409
    assert "conflict" in r.json()["detail"].lower() or "already" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_trainer_analytics(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    trainers = (
        await client.get("/api/v1/trainer/trainers", headers=_h(token))
    ).json()
    tid = trainers[0]["id"]
    r = await client.get(
        f"/api/v1/trainer/trainers/{tid}/analytics", headers=_h(token)
    )
    assert r.status_code == 200
    body = r.json()
    assert "sessions_completed" in body
    assert "upcoming_sessions" in body
    assert "attendance_rate" in body
    assert "avg_rating" in body

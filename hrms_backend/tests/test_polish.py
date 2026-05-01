"""Phase 17 polish features tests."""
from datetime import datetime, timedelta

import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Assets ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_seeded_assets(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/polish/assets", headers=_h(token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 5
    in_stock = [a for a in rows if a["status"] == "in_stock"]
    assigned = [a for a in rows if a["status"] == "assigned"]
    assert in_stock and assigned


@pytest.mark.asyncio
async def test_my_assets_employee_view(client):
    """JKT018 (employee@) was assigned a Dell laptop in the seeder."""
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/polish/assets/me", headers=_h(token))
    assert r.status_code == 200
    mine = r.json()
    assert any(a["asset_tag"] == "JKT-LAP-002" for a in mine)


@pytest.mark.asyncio
async def test_assign_and_return_flow(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    employees = (
        await client.get("/api/v1/employees", headers=_h(hr_token))
    ).json()
    employee_demo = next(e for e in employees if e["employee_code"] == "JKT018")

    # Create a fresh asset
    r = await client.post(
        "/api/v1/polish/assets",
        headers=_h(hr_token),
        json={
            "asset_tag": "TEST-LAP-X",
            "name": "Test laptop",
            "category": "laptop",
        },
    )
    assert r.status_code == 201, r.text
    asset_id = r.json()["id"]

    # Assign
    r = await client.post(
        f"/api/v1/polish/assets/{asset_id}/assign",
        headers=_h(hr_token),
        json={"employee_id": employee_demo["id"], "notes": "Spare unit"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "assigned"
    assert r.json()["assigned_to"] == employee_demo["id"]

    # Cannot re-assign (in 'assigned' state)
    r = await client.post(
        f"/api/v1/polish/assets/{asset_id}/assign",
        headers=_h(hr_token),
        json={"employee_id": employee_demo["id"]},
    )
    assert r.status_code == 422

    # Return damaged → in_repair
    r = await client.post(
        f"/api/v1/polish/assets/{asset_id}/return",
        headers=_h(hr_token),
        json={"return_condition": "damaged", "notes": "Cracked screen"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "in_repair"
    assert body["condition"] == "damaged"
    assert body["assigned_to"] is None

    # History should show the assignment + return
    r = await client.get(
        f"/api/v1/polish/assets/{asset_id}/history", headers=_h(hr_token)
    )
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 1
    assert history[0]["return_condition"] == "damaged"


# ── Visitors ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_visitor_pre_register_and_check_in(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    expected = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    r = await client.post(
        "/api/v1/polish/visitors",
        headers=_h(emp_token),
        json={
            "full_name": "Ravi Kumar",
            "purpose": "Vendor meeting",
            "expected_at": expected,
            "company": "Acme Corp",
        },
    )
    assert r.status_code == 201, r.text
    visitor = r.json()
    qr = visitor["qr_token"]
    assert visitor["status"] == "scheduled"

    # Reception (HR/admin) checks them in
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/polish/visitors/check-in",
        headers=_h(hr_token),
        json={"qr_token": qr, "badge_number": "B-101"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "checked_in"
    assert r.json()["badge_number"] == "B-101"

    # Check out
    r = await client.post(
        f"/api/v1/polish/visitors/{visitor['id']}/check-out",
        headers=_h(hr_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "checked_out"

    # Wrong QR
    r = await client.post(
        "/api/v1/polish/visitors/check-in",
        headers=_h(hr_token),
        json={"qr_token": "bogus"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_employee_can_only_see_their_own_visitors(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    expected = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    await client.post(
        "/api/v1/polish/visitors",
        headers=_h(emp_token),
        json={
            "full_name": "Self Visitor",
            "purpose": "Demo",
            "expected_at": expected,
        },
    )

    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/polish/visitors/me", headers=_h(mgr_token))
    assert r.status_code == 200
    assert all(v["full_name"] != "Self Visitor" for v in r.json())


# ── Meeting rooms ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_room_booking_conflict_detection(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    rooms = (
        await client.get("/api/v1/polish/rooms", headers=_h(emp_token))
    ).json()
    assert len(rooms) >= 1
    room = rooms[0]

    start = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
    end = start + timedelta(hours=1)

    r = await client.post(
        "/api/v1/polish/rooms/bookings",
        headers=_h(emp_token),
        json={
            "room_id": room["id"],
            "title": "Sprint planning",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert r.status_code == 201, r.text
    booking_id = r.json()["id"]

    # Overlapping booking → conflict
    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.post(
        "/api/v1/polish/rooms/bookings",
        headers=_h(mgr_token),
        json={
            "room_id": room["id"],
            "title": "Roadmap",
            "start_time": (start + timedelta(minutes=30)).isoformat(),
            "end_time": (end + timedelta(minutes=30)).isoformat(),
        },
    )
    assert r.status_code == 409

    # End before start → 422
    r = await client.post(
        "/api/v1/polish/rooms/bookings",
        headers=_h(emp_token),
        json={
            "room_id": room["id"],
            "title": "Bad",
            "start_time": end.isoformat(),
            "end_time": start.isoformat(),
        },
    )
    assert r.status_code == 422

    # Cancel my booking
    r = await client.post(
        f"/api/v1/polish/rooms/bookings/{booking_id}/cancel",
        headers=_h(emp_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    # After cancellation, the slot is free → manager can book
    r = await client.post(
        "/api/v1/polish/rooms/bookings",
        headers=_h(mgr_token),
        json={
            "room_id": room["id"],
            "title": "Roadmap",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert r.status_code == 201

    # A different employee cannot cancel manager's booking
    new_id = r.json()["id"]
    r = await client.post(
        f"/api/v1/polish/rooms/bookings/{new_id}/cancel",
        headers=_h(emp_token),
    )
    assert r.status_code == 403


# ── Internal job postings ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_apply_to_seeded_posting_and_referral(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    listings = (
        await client.get(
            "/api/v1/polish/jobs?status=published", headers=_h(emp_token)
        )
    ).json()
    posting = next(p for p in listings if p["code"] == "JKT-IJP-DEV-001")

    # Self-referral blocked
    employees = (
        await client.get("/api/v1/employees", headers=_h(emp_token))
    ).json()
    me = next(e for e in employees if e["employee_code"] == "JKT018")
    pooja = next(e for e in employees if e["employee_code"] == "JKT014")

    r = await client.post(
        f"/api/v1/polish/jobs/{posting['id']}/apply",
        headers=_h(emp_token),
        json={
            "referrer_employee_id": me["id"],
            "cover_note": "I'd be great for this",
        },
    )
    assert r.status_code == 422

    # Apply with Pooja as referrer
    r = await client.post(
        f"/api/v1/polish/jobs/{posting['id']}/apply",
        headers=_h(emp_token),
        json={
            "referrer_employee_id": pooja["id"],
            "cover_note": "Excited to step up",
        },
    )
    assert r.status_code == 201, r.text
    application_id = r.json()["id"]

    # Duplicate application blocked
    r = await client.post(
        f"/api/v1/polish/jobs/{posting['id']}/apply",
        headers=_h(emp_token),
        json={"cover_note": "Again"},
    )
    assert r.status_code == 409

    # Pooja sees this in her referrals
    pooja_token = await _login(client, "pooja@jaikalki.com", "Password@123")
    r = await client.get(
        "/api/v1/polish/jobs/me/referrals", headers=_h(pooja_token)
    )
    assert r.status_code == 200
    assert any(a["id"] == application_id for a in r.json())

    # HR moves through the funnel
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    for s in ("shortlisted", "interviewing", "hired"):
        r = await client.patch(
            f"/api/v1/polish/jobs/applications/{application_id}/status",
            headers=_h(hr_token),
            json={"status": s},
        )
        assert r.status_code == 200, r.text
    assert r.json()["status"] == "hired"


@pytest.mark.asyncio
async def test_apply_to_draft_posting_blocked(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/polish/jobs",
        headers=_h(hr_token),
        json={
            "code": "TEST-DRAFT-1",
            "title": "Draft role",
            "employment_type": "full_time",
        },
    )
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["status"] == "draft"

    emp_token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        f"/api/v1/polish/jobs/{pid}/apply",
        headers=_h(emp_token),
        json={},
    )
    assert r.status_code == 422

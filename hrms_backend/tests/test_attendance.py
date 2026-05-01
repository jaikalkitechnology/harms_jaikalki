"""Phase 3 attendance tests."""
import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_geofence_distance_unit():
    from app.utils.geo import haversine_distance_m, check_office_geofence

    # Same point → 0
    assert haversine_distance_m(0, 0, 0, 0) == 0

    # ~111 km between latitudes 1 degree apart
    d = haversine_distance_m(0, 0, 1, 0)
    assert 110_000 < d < 112_000

    # check_office_geofence: very close to office → inside
    inside = check_office_geofence(19.2853, 72.8533)
    assert inside.inside is True
    assert inside.distance_m < 50

    # Mumbai Marine Drive (~25 km from office) → outside
    outside = check_office_geofence(18.945, 72.823)
    assert outside.inside is False


@pytest.mark.asyncio
async def test_check_in_inside_geofence_succeeds(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/attendance/check-in",
        headers=_h(token),
        json={"lat": 19.2853, "lng": 72.8533, "work_mode": "office"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "present"
    assert body["check_in_distance_m"] is not None
    assert body["check_in_distance_m"] < 50


@pytest.mark.asyncio
async def test_check_in_outside_geofence_blocked(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    # Far away location (Marine Drive)
    r = await client.post(
        "/api/v1/attendance/check-in",
        headers=_h(token),
        json={"lat": 18.945, "lng": 72.823, "work_mode": "office"},
    )
    assert r.status_code == 422
    assert "geo-fence" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_wfh_check_in_requires_selfie(client):
    token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.post(
        "/api/v1/attendance/check-in",
        headers=_h(token),
        json={"lat": 19.0, "lng": 72.0, "work_mode": "wfh"},
    )
    assert r.status_code == 422

    r = await client.post(
        "/api/v1/attendance/check-in",
        headers=_h(token),
        json={
            "lat": 19.0,
            "lng": 72.0,
            "work_mode": "wfh",
            "selfie_url": "https://example.com/selfie.jpg",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "wfh"


@pytest.mark.asyncio
async def test_double_check_in_blocked(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r1 = await client.post(
        "/api/v1/attendance/check-in",
        headers=_h(token),
        json={"lat": 19.2853, "lng": 72.8533, "work_mode": "office"},
    )
    assert r1.status_code == 200
    r2 = await client.post(
        "/api/v1/attendance/check-in",
        headers=_h(token),
        json={"lat": 19.2853, "lng": 72.8533, "work_mode": "office"},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_regularization_flow(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/attendance/regularize",
        headers=_h(emp_token),
        json={
            "date": "2026-04-15",
            "requested_check_in": "2026-04-15T09:00:00",
            "requested_check_out": "2026-04-15T18:00:00",
            "reason": "Forgot to mark attendance, working from office",
        },
    )
    assert r.status_code == 201, r.text
    reg_id = r.json()["id"]

    hr_token = await _login(client, "hr@hrms.com", "hr123")
    pending = (
        await client.get(
            "/api/v1/attendance/regularize/pending", headers=_h(hr_token)
        )
    ).json()
    assert any(p["id"] == reg_id for p in pending)

    r = await client.post(
        f"/api/v1/attendance/regularize/{reg_id}/approve",
        headers=_h(hr_token),
        json={"decision_comment": "Approved"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

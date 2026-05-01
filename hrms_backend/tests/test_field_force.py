"""Phase 9 field force tests."""
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
async def test_seeded_field_employee_has_today_jobs(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    r = await client.get("/api/v1/field/jobs/today", headers=_h(token))
    assert r.status_code == 200, r.text
    jobs = r.json()
    assert len(jobs) == 4
    assert {j["status"] for j in jobs} == {"scheduled"}
    assert all(j["customer"]["name"] for j in jobs)


@pytest.mark.asyncio
async def test_customer_crud(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/field/customers",
        headers=_h(hr_token),
        json={
            "name": "Test Trader",
            "type": "lead",
            "city": "Pune",
            "geo_lat": 18.5204,
            "geo_lng": 73.8567,
        },
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    r = await client.get(f"/api/v1/field/customers/{cid}", headers=_h(hr_token))
    assert r.status_code == 200
    assert r.json()["name"] == "Test Trader"

    r = await client.patch(
        f"/api/v1/field/customers/{cid}",
        headers=_h(hr_token),
        json={"type": "prospect"},
    )
    assert r.status_code == 200
    assert r.json()["type"] == "prospect"


@pytest.mark.asyncio
async def test_visit_lifecycle_inside_geofence(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    jobs = (await client.get("/api/v1/field/jobs/today", headers=_h(token))).json()
    job = jobs[0]
    cust = job["customer"]

    # Check in at the customer's location with selfie
    r = await client.post(
        f"/api/v1/field/jobs/{job['id']}/checkin",
        headers=_h(token),
        json={
            "lat": float(cust["geo_lat"]),
            "lng": float(cust["geo_lng"]),
            "is_mock": False,
            "selfie_url": "https://example.com/selfie.jpg",
        },
    )
    assert r.status_code == 200, r.text
    visit = r.json()
    assert visit["check_in_distance_m"] is not None
    assert visit["check_in_distance_m"] < 50
    visit_id = visit["id"]

    # Submit form
    r = await client.post(
        f"/api/v1/field/visits/{visit_id}/visit-form",
        headers=_h(token),
        json={"visit_form": {"competitor_seen": "ABC", "stock_level": "low"}},
    )
    assert r.status_code == 200
    assert r.json()["visit_form"]["stock_level"] == "low"

    # Add a photo
    r = await client.post(
        f"/api/v1/field/visits/{visit_id}/photos",
        headers=_h(token),
        json={
            "photo_url": "https://example.com/storefront.jpg",
            "photo_type": "storefront",
            "geo_lat": float(cust["geo_lat"]),
            "geo_lng": float(cust["geo_lng"]),
            "watermarked": True,
        },
    )
    assert r.status_code == 201, r.text

    # Check out
    r = await client.post(
        f"/api/v1/field/visits/{visit_id}/checkout",
        headers=_h(token),
        json={
            "lat": float(cust["geo_lat"]),
            "lng": float(cust["geo_lng"]),
            "outcome": "order_placed",
            "notes": "Customer placed an order",
            "signature_url": "https://example.com/sig.png",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["outcome"] == "order_placed"
    assert body["signature_url"]
    assert len(body["photos"]) == 1


@pytest.mark.asyncio
async def test_visit_check_in_outside_geofence_blocked(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    jobs = (await client.get("/api/v1/field/jobs/today", headers=_h(token))).json()
    job = jobs[0]

    # Far-away coordinates → should fail
    r = await client.post(
        f"/api/v1/field/jobs/{job['id']}/checkin",
        headers=_h(token),
        json={
            "lat": 28.6139,  # Delhi
            "lng": 77.2090,
            "is_mock": False,
            "selfie_url": "https://example.com/selfie.jpg",
        },
    )
    assert r.status_code == 422
    assert "geo-fence" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_visit_check_in_mock_gps_blocked(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    jobs = (await client.get("/api/v1/field/jobs/today", headers=_h(token))).json()
    job = jobs[0]
    cust = job["customer"]

    r = await client.post(
        f"/api/v1/field/jobs/{job['id']}/checkin",
        headers=_h(token),
        json={
            "lat": float(cust["geo_lat"]),
            "lng": float(cust["geo_lng"]),
            "is_mock": True,
            "selfie_url": "https://example.com/selfie.jpg",
        },
    )
    assert r.status_code == 422
    assert "mock" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_visit_check_in_requires_selfie(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    jobs = (await client.get("/api/v1/field/jobs/today", headers=_h(token))).json()
    job = jobs[0]
    cust = job["customer"]

    r = await client.post(
        f"/api/v1/field/jobs/{job['id']}/checkin",
        headers=_h(token),
        json={
            "lat": float(cust["geo_lat"]),
            "lng": float(cust["geo_lng"]),
            "is_mock": False,
        },
    )
    assert r.status_code == 422
    assert "selfie" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_location_track_and_live_map(client):
    field_token = await _login(client, "jkt019@jaikalki.com", "Password@123")

    r = await client.post(
        "/api/v1/field/location/track",
        headers=_h(field_token),
        json={
            "lat": 12.9716,
            "lng": 77.5946,
            "accuracy_m": 8,
            "battery_pct": 73,
            "is_mock": False,
        },
    )
    assert r.status_code == 201, r.text

    # Mock GPS rejected
    r = await client.post(
        "/api/v1/field/location/track",
        headers=_h(field_token),
        json={
            "lat": 12.9716,
            "lng": 77.5946,
            "is_mock": True,
        },
    )
    assert r.status_code == 422

    # Manager-style live map (HR sees all field employees)
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/field/team/live-map", headers=_h(hr_token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert any(row["employee_code"] == "JKT019" for row in rows)
    me = next(row for row in rows if row["employee_code"] == "JKT019")
    assert abs(me["lat"] - 12.9716) < 0.0001
    assert me["battery_pct"] == 73


@pytest.mark.asyncio
async def test_team_performance(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/field/team/performance", headers=_h(hr_token))
    assert r.status_code == 200
    rows = r.json()
    me = next(row for row in rows if row["employee_code"] == "JKT019")
    assert me["jobs_assigned"] == 4

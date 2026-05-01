"""Phase 16 reports & analytics tests."""
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
async def test_employee_cannot_view_reports(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/reports/headcount", headers=_h(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_headcount_trend(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get(
        "/api/v1/reports/headcount?months=12", headers=_h(token)
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["months"] == 12
    assert isinstance(body["points"], list)
    assert body["current_headcount"] >= 1


@pytest.mark.asyncio
async def test_attrition_zero_for_seeded_data(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get(
        "/api/v1/reports/attrition?months=12", headers=_h(token)
    )
    assert r.status_code == 200
    body = r.json()
    assert body["exits"] == 0
    assert body["attrition_pct"] == 0.0


@pytest.mark.asyncio
async def test_department_breakdown(client):
    token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get(
        "/api/v1/reports/department-breakdown", headers=_h(token)
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert all("department" in r and "headcount" in r for r in rows)


@pytest.mark.asyncio
async def test_attendance_snapshot(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/reports/attendance", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total_employees"] >= 1
    assert (
        body["present"] + body["wfh"] + body["leave"]
        + body["absent"] + body["holiday"]
    ) == body["total_employees"]


@pytest.mark.asyncio
async def test_compliance_overview(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/reports/compliance", headers=_h(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mandatory_courses"] >= 2
    assert body["employees_total"] >= 1
    # Nobody is enrolled in mandatory courses by default → 0 fully compliant
    assert body["fully_compliant"] == 0
    assert body["coverage_pct"] == 0.0


@pytest.mark.asyncio
async def test_sales_overview_includes_seed(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/reports/sales", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    # 4 seeded leads exist
    assert body["leads_count"] >= 4


@pytest.mark.asyncio
async def test_verification_stats(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/reports/verification", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 2  # seeded jobs


@pytest.mark.asyncio
async def test_training_stats(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/reports/training", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    assert body["sessions_total"] >= 2


@pytest.mark.asyncio
async def test_performance_returns_active_cycle(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/reports/performance", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    assert body is not None
    assert body["cycle_name"].startswith("Q2 2026") or "Q" in body["cycle_name"]


@pytest.mark.asyncio
async def test_director_dashboard_composite(client):
    token = await _login(client, "admin@hrms.com", "admin123")
    r = await client.get(
        "/api/v1/reports/director-dashboard", headers=_h(token)
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert {
        "headcount",
        "attrition",
        "department_breakdown",
        "compliance",
        "verification",
        "training",
    } <= set(body)


@pytest.mark.asyncio
async def test_saved_report_lifecycle(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")

    r = await client.post(
        "/api/v1/reports/saved",
        headers=_h(hr_token),
        json={
            "code": "RPT-HC-12M",
            "name": "Headcount 12 months",
            "report_type": "headcount",
            "filters": {"months": 12},
            "is_shared": True,
        },
    )
    assert r.status_code == 201, r.text
    rid = r.json()["id"]

    # Duplicate code → conflict
    r = await client.post(
        "/api/v1/reports/saved",
        headers=_h(hr_token),
        json={
            "code": "RPT-HC-12M",
            "name": "Dup",
            "report_type": "headcount",
        },
    )
    assert r.status_code == 409

    # HR sees their own
    r = await client.get("/api/v1/reports/saved", headers=_h(hr_token))
    assert any(s["id"] == rid for s in r.json())

    # Other users see shared ones
    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/reports/saved", headers=_h(mgr_token))
    assert any(s["id"] == rid for s in r.json())

    # Non-creator cannot delete
    r = await client.delete(
        f"/api/v1/reports/saved/{rid}", headers=_h(mgr_token)
    )
    assert r.status_code == 403

    # Creator can delete
    r = await client.delete(
        f"/api/v1/reports/saved/{rid}", headers=_h(hr_token)
    )
    assert r.status_code == 204

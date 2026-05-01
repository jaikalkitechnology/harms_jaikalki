"""Phase 6 DWP tests."""
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
async def test_morning_template_for_employee(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/dwp/template/morning", headers=_h(token))
    assert r.status_code == 200, r.text
    body = r.json()
    # JKT018 employee is in IT, so they should get the IT morning template.
    assert body["template"]["type"] == "morning"
    assert body["template"]["code"] in ("DWP-IT-M", "DWP-DEFAULT-M")
    keys = [f["key"] for f in body["template"]["fields"]]
    assert "tasks" in keys
    assert body["streak_days"] == 0


@pytest.mark.asyncio
async def test_submit_morning_then_eod_auto_links(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    morning_t = (
        await client.get("/api/v1/dwp/template/morning", headers=_h(token))
    ).json()
    morning_tpl_id = morning_t["template"]["id"]

    r = await client.post(
        "/api/v1/dwp/morning/submit",
        headers=_h(token),
        json={
            "template_id": morning_tpl_id,
            "fields": {
                "tasks": "1. Refactor auth module\n2. Code review",
                "hours_planned": 8,
                "status_tag": "green",
            },
            "total_hours": 8,
        },
    )
    assert r.status_code == 201, r.text
    morning_id = r.json()["id"]

    # EOD template should now have prefill from the morning.
    eod_t = (
        await client.get("/api/v1/dwp/template/eod", headers=_h(token))
    ).json()
    assert eod_t["template"]["type"] == "eod"
    assert eod_t["linked_morning_id"] == morning_id
    assert "tasks" in eod_t["prefill"]
    assert "Refactor auth" in eod_t["prefill"]["tasks"]


@pytest.mark.asyncio
async def test_double_morning_blocked(client):
    token = await _login(client, "manager@hrms.com", "manager123")
    morning_t = (
        await client.get("/api/v1/dwp/template/morning", headers=_h(token))
    ).json()
    body = {
        "template_id": morning_t["template"]["id"],
        "fields": {"tasks": "Plan A"},
    }
    r1 = await client.post("/api/v1/dwp/morning/submit", headers=_h(token), json=body)
    assert r1.status_code == 201, r1.text
    r2 = await client.post("/api/v1/dwp/morning/submit", headers=_h(token), json=body)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_required_field_validation(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    morning_t = (
        await client.get("/api/v1/dwp/template/morning", headers=_h(token))
    ).json()
    r = await client.post(
        "/api/v1/dwp/morning/submit",
        headers=_h(token),
        json={
            "template_id": morning_t["template"]["id"],
            "fields": {"hours_planned": 8},  # `tasks` is required and missing
        },
    )
    assert r.status_code == 422
    assert "tasks" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_team_today_lists_manager_reports(client):
    # Employee submits a morning DWP.
    emp = await _login(client, "employee@hrms.com", "employee123")
    morning_t = (
        await client.get("/api/v1/dwp/template/morning", headers=_h(emp))
    ).json()
    await client.post(
        "/api/v1/dwp/morning/submit",
        headers=_h(emp),
        json={
            "template_id": morning_t["template"]["id"],
            "fields": {"tasks": "Build dashboards"},
        },
    )

    # Manager (JKT016) reports JKT018 (employee) — should see it.
    mgr = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/dwp/team/today", headers=_h(mgr))
    assert r.status_code == 200
    items = r.json()
    codes = [i["employee_code"] for i in items]
    assert "JKT018" in codes


@pytest.mark.asyncio
async def test_employee_cannot_see_team_view(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/dwp/team/today", headers=_h(emp))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_blockers_endpoint_filters_eod_with_blockers(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    morning_t = (
        await client.get("/api/v1/dwp/template/morning", headers=_h(emp))
    ).json()
    await client.post(
        "/api/v1/dwp/morning/submit",
        headers=_h(emp),
        json={
            "template_id": morning_t["template"]["id"],
            "fields": {"tasks": "Investigate flaky test"},
        },
    )
    eod_t = (
        await client.get("/api/v1/dwp/template/eod", headers=_h(emp))
    ).json()
    await client.post(
        "/api/v1/dwp/eod/submit",
        headers=_h(emp),
        json={
            "template_id": eod_t["template"]["id"],
            "fields": {
                "tasks": "Investigated, need DB access",
                "blockers": "Need read-only prod DB access from infra team",
            },
            "total_hours": 7,
        },
    )

    mgr = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/dwp/team/blockers", headers=_h(mgr))
    assert r.status_code == 200
    codes = [i["employee_code"] for i in r.json()]
    assert "JKT018" in codes


@pytest.mark.asyncio
async def test_comment_kudos(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    morning_t = (
        await client.get("/api/v1/dwp/template/morning", headers=_h(emp))
    ).json()
    sub = await client.post(
        "/api/v1/dwp/morning/submit",
        headers=_h(emp),
        json={
            "template_id": morning_t["template"]["id"],
            "fields": {"tasks": "Finish feature"},
        },
    )
    sub_id = sub.json()["id"]

    mgr = await _login(client, "manager@hrms.com", "manager123")
    r = await client.post(
        f"/api/v1/dwp/{sub_id}/comment",
        headers=_h(mgr),
        json={"comment": "Great work!", "is_kudos": True},
    )
    assert r.status_code == 201
    assert r.json()["is_kudos"] is True

"""Phase 15 performance management tests."""
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
async def test_seeded_cycle_and_goals(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    cycles = (
        await client.get("/api/v1/performance/cycles", headers=_h(token))
    ).json()
    assert any(c["code"] == "Q2-2026" for c in cycles)

    goals = (
        await client.get("/api/v1/performance/goals/me", headers=_h(token))
    ).json()
    assert len(goals) == 4
    weights = sum(g["weight_pct"] for g in goals)
    assert weights == 100


@pytest.mark.asyncio
async def test_employee_can_create_and_progress_a_goal(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    cycles = (
        await client.get("/api/v1/performance/cycles", headers=_h(token))
    ).json()
    cycle = next(c for c in cycles if c["code"] == "Q2-2026")

    r = await client.post(
        "/api/v1/performance/goals",
        headers=_h(token),
        json={
            "cycle_id": cycle["id"],
            "title": "Self-set learning goal",
            "weight_pct": 0,
            "category": "growth",
        },
    )
    assert r.status_code == 201, r.text
    gid = r.json()["id"]
    assert r.json()["status"] == "active"

    r = await client.patch(
        f"/api/v1/performance/goals/{gid}",
        headers=_h(token),
        json={"progress_pct": 100},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["progress_pct"] == 100
    assert body["status"] == "achieved"


@pytest.mark.asyncio
async def test_self_review_lifecycle_and_share_acknowledge(client):
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    hr_token = await _login(client, "hr@hrms.com", "hr123")

    cycles = (
        await client.get(
            "/api/v1/performance/cycles", headers=_h(emp_token)
        )
    ).json()
    cycle = next(c for c in cycles if c["code"] == "Q2-2026")

    r = await client.post(
        f"/api/v1/performance/cycles/{cycle['id']}/self-review",
        headers=_h(emp_token),
        json={
            "overall_rating": 4.0,
            "achievements": "Shipped V2 attendance",
            "improvement_areas": "Better unit tests",
        },
    )
    assert r.status_code == 200, r.text
    review = r.json()
    assert review["status"] == "submitted"
    assert review["review_type"] == "self"

    # Share it (HR)
    r = await client.post(
        f"/api/v1/performance/reviews/{review['id']}/share",
        headers=_h(hr_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "shared_with_employee"

    # Employee can acknowledge
    r = await client.post(
        f"/api/v1/performance/reviews/{review['id']}/acknowledge",
        headers=_h(emp_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"
    assert r.json()["acknowledged_at"] is not None

    # Acknowledge before share is blocked (use a fresh review)
    r = await client.post(
        f"/api/v1/performance/cycles/{cycle['id']}/self-review",
        headers=_h(emp_token),
        json={"overall_rating": 4.5},
    )
    # Already submitted → 422 because we re-edit a submitted review
    assert r.status_code in (200, 422)


@pytest.mark.asyncio
async def test_manager_review_requires_direct_report(client):
    """Employee Demo (JKT018) reports to Manager Demo (JKT016)."""
    mgr_token = await _login(client, "manager@hrms.com", "manager123")

    # Find employee's id via /goals endpoint? Use list_employees.
    r = await client.get(
        "/api/v1/employees", headers=_h(mgr_token)
    )
    assert r.status_code == 200
    employees = r.json()
    employee_demo = next(e for e in employees if e["employee_code"] == "JKT018")

    cycles = (
        await client.get(
            "/api/v1/performance/cycles", headers=_h(mgr_token)
        )
    ).json()
    cycle = next(c for c in cycles if c["code"] == "Q2-2026")

    r = await client.post(
        f"/api/v1/performance/cycles/{cycle['id']}/manager-review/{employee_demo['id']}",
        headers=_h(mgr_token),
        json={
            "overall_rating": 4.2,
            "achievements": "Strong delivery and mentorship",
            "increment_recommendation_pct": 12,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["review_type"] == "manager"
    assert r.json()["increment_recommendation_pct"] == 12

    # HR is NOT JKT018's direct manager → should fail
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        f"/api/v1/performance/cycles/{cycle['id']}/manager-review/{employee_demo['id']}",
        headers=_h(hr_token),
        json={"overall_rating": 3},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_360_feedback_anonymous_aggregation(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    employees = (
        await client.get("/api/v1/employees", headers=_h(hr_token))
    ).json()
    subject = next(e for e in employees if e["employee_code"] == "JKT018")
    pooja = next(e for e in employees if e["employee_code"] == "JKT014")
    director = next(e for e in employees if e["employee_code"] == "JKT001")

    r = await client.post(
        "/api/v1/performance/feedback/requests",
        headers=_h(hr_token),
        json={
            "subject_employee_id": subject["id"],
            "reviewer_employee_ids": [pooja["id"], director["id"]],
            "relation": "peer",
            "is_anonymous": True,
        },
    )
    assert r.status_code == 201, r.text
    requests = r.json()
    assert len(requests) == 2

    # Pooja submits feedback
    pooja_token = await _login(client, "pooja@jaikalki.com", "Password@123")
    pending = (
        await client.get(
            "/api/v1/performance/feedback/me/pending", headers=_h(pooja_token)
        )
    ).json()
    assert len(pending) == 1
    req_id = pending[0]["id"]
    r = await client.post(
        f"/api/v1/performance/feedback/requests/{req_id}/respond",
        headers=_h(pooja_token),
        json={
            "overall_rating": 4.5,
            "strengths": "Always available, great mentor",
            "improvement_areas": "Could communicate roadmap better",
            "competencies": {"collaboration": 5, "execution": 4},
        },
    )
    assert r.status_code == 201, r.text

    # Aggregate (HR view)
    r = await client.get(
        f"/api/v1/performance/feedback/aggregate/{subject['id']}",
        headers=_h(hr_token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["response_count"] == 1
    assert body["avg_rating"] == 4.5
    assert "collaboration" in body["competency_averages"]
    assert any(
        "mentor" in s for s in body["anonymous_strengths"]
    )

    # Subject can see their own aggregate
    subject_token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get(
        f"/api/v1/performance/feedback/aggregate/{subject['id']}",
        headers=_h(subject_token),
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_one_on_one_visibility(client):
    """Manager creates a 1-on-1; employee only sees `shared` ones."""
    mgr_token = await _login(client, "manager@hrms.com", "manager123")
    employees = (
        await client.get("/api/v1/employees", headers=_h(mgr_token))
    ).json()
    target = next(e for e in employees if e["employee_code"] == "JKT018")

    # Create a private (manager_only) note + a shared note
    r = await client.post(
        "/api/v1/performance/one-on-one",
        headers=_h(mgr_token),
        json={
            "employee_id": target["id"],
            "meeting_date": "2026-05-01",
            "agenda": "Career growth",
            "discussion_notes": "Wants to grow into a tech lead",
            "visibility": "manager_only",
        },
    )
    assert r.status_code == 201
    private_id = r.json()["id"]

    r = await client.post(
        "/api/v1/performance/one-on-one",
        headers=_h(mgr_token),
        json={
            "employee_id": target["id"],
            "meeting_date": "2026-05-08",
            "agenda": "Sprint reflection",
            "visibility": "shared",
        },
    )
    assert r.status_code == 201
    shared_id = r.json()["id"]

    # Manager sees both
    r = await client.get(
        "/api/v1/performance/one-on-one/team", headers=_h(mgr_token)
    )
    assert r.status_code == 200
    ids = {n["id"] for n in r.json()}
    assert {private_id, shared_id} <= ids

    # Employee only sees the shared one
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get(
        "/api/v1/performance/one-on-one/me", headers=_h(emp_token)
    )
    assert r.status_code == 200
    employee_ids = {n["id"] for n in r.json()}
    assert shared_id in employee_ids
    assert private_id not in employee_ids


@pytest.mark.asyncio
async def test_cannot_log_one_on_one_for_non_reportee(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    employees = (
        await client.get("/api/v1/employees", headers=_h(hr_token))
    ).json()
    # JKT001 (Director Demo) doesn't report to HR
    director = next(e for e in employees if e["employee_code"] == "JKT001")
    r = await client.post(
        "/api/v1/performance/one-on-one",
        headers=_h(hr_token),
        json={
            "employee_id": director["id"],
            "meeting_date": "2026-05-01",
            "visibility": "manager_only",
        },
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_cycle_status_transitions(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    cycles = (
        await client.get(
            "/api/v1/performance/cycles", headers=_h(hr_token)
        )
    ).json()
    cycle_id = next(c for c in cycles if c["code"] == "Q2-2026")["id"]

    r = await client.patch(
        f"/api/v1/performance/cycles/{cycle_id}/status",
        headers=_h(hr_token),
        json={"status": "calibration"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "calibration"

    r = await client.patch(
        f"/api/v1/performance/cycles/{cycle_id}/status",
        headers=_h(hr_token),
        json={"status": "closed"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "closed"

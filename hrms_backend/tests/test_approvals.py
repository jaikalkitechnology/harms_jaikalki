"""Phase 4 universal approval engine tests."""
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
async def test_applying_leave_creates_universal_approval(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    types = (await client.get("/api/v1/leaves/types", headers=_h(emp))).json()
    cl = next(t for t in types if t["code"] == "CL")

    r = await client.post(
        "/api/v1/leaves/apply",
        headers=_h(emp),
        json={
            "leave_type_id": cl["id"],
            "from_date": "2026-07-13",
            "to_date": "2026-07-13",
            "reason": "Universal approval test",
        },
    )
    assert r.status_code == 201
    leave_id = r.json()["id"]

    mgr = await _login(client, "manager@hrms.com", "manager123")
    inbox = (await client.get("/api/v1/approvals/inbox", headers=_h(mgr))).json()
    matching = [
        a for a in inbox
        if a["request_type"] == "leave_request" and a["request_id"] == leave_id
    ]
    assert len(matching) == 1
    assert matching[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_universal_approve_decides_underlying_leave(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    types = (await client.get("/api/v1/leaves/types", headers=_h(emp))).json()
    cl = next(t for t in types if t["code"] == "CL")

    r = await client.post(
        "/api/v1/leaves/apply",
        headers=_h(emp),
        json={
            "leave_type_id": cl["id"],
            "from_date": "2026-07-20",
            "to_date": "2026-07-21",
            "reason": "Approve via universal",
        },
    )
    leave_id = r.json()["id"]

    mgr = await _login(client, "manager@hrms.com", "manager123")
    inbox = (await client.get("/api/v1/approvals/inbox", headers=_h(mgr))).json()
    approval = next(
        a for a in inbox
        if a["request_type"] == "leave_request" and a["request_id"] == leave_id
    )

    r = await client.post(
        f"/api/v1/approvals/{approval['id']}/approve",
        headers=_h(mgr),
        json={"comments": "Looks good"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "approved"
    assert body["actions"][-1]["action"] == "approved"

    # Underlying leave is approved.
    my = (await client.get("/api/v1/leaves/requests", headers=_h(emp))).json()
    leave = next(l for l in my if l["id"] == leave_id)
    assert leave["status"] == "approved"


@pytest.mark.asyncio
async def test_universal_reject_propagates(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    types = (await client.get("/api/v1/leaves/types", headers=_h(emp))).json()
    cl = next(t for t in types if t["code"] == "CL")

    leave_id = (
        await client.post(
            "/api/v1/leaves/apply",
            headers=_h(emp),
            json={
                "leave_type_id": cl["id"],
                "from_date": "2026-08-03",
                "to_date": "2026-08-03",
                "reason": "Reject test",
            },
        )
    ).json()["id"]

    mgr = await _login(client, "manager@hrms.com", "manager123")
    inbox = (await client.get("/api/v1/approvals/inbox", headers=_h(mgr))).json()
    aid = next(
        a["id"] for a in inbox
        if a["request_type"] == "leave_request" and a["request_id"] == leave_id
    )

    r = await client.post(
        f"/api/v1/approvals/{aid}/reject",
        headers=_h(mgr),
        json={"comments": "Workload"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"

    my = (await client.get("/api/v1/leaves/requests", headers=_h(emp))).json()
    assert next(l["status"] for l in my if l["id"] == leave_id) == "rejected"


@pytest.mark.asyncio
async def test_legacy_endpoint_syncs_universal_approval(client):
    """Approving via the old /leaves/{id}/approve also resolves the Approval."""
    emp = await _login(client, "employee@hrms.com", "employee123")
    types = (await client.get("/api/v1/leaves/types", headers=_h(emp))).json()
    cl = next(t for t in types if t["code"] == "CL")

    leave_id = (
        await client.post(
            "/api/v1/leaves/apply",
            headers=_h(emp),
            json={
                "leave_type_id": cl["id"],
                "from_date": "2026-09-09",
                "to_date": "2026-09-09",
                "reason": "Legacy decide",
            },
        )
    ).json()["id"]

    mgr = await _login(client, "manager@hrms.com", "manager123")
    # Use the original endpoint (Phase 3).
    r = await client.post(
        f"/api/v1/leaves/{leave_id}/approve",
        headers=_h(mgr),
        json={"decision_comment": "Legacy approve"},
    )
    assert r.status_code == 200

    # The matching Approval should now be finalised.
    inbox = (await client.get("/api/v1/approvals/inbox", headers=_h(mgr))).json()
    assert not any(
        a["request_id"] == leave_id and a["request_type"] == "leave_request"
        for a in inbox
    )


@pytest.mark.asyncio
async def test_inbox_counts_groups_by_type(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    types = (await client.get("/api/v1/leaves/types", headers=_h(emp))).json()
    cl = next(t for t in types if t["code"] == "CL")

    # Apply a leave so there's at least one pending of leave_request.
    await client.post(
        "/api/v1/leaves/apply",
        headers=_h(emp),
        json={
            "leave_type_id": cl["id"],
            "from_date": "2026-10-12",
            "to_date": "2026-10-12",
            "reason": "Counts test",
        },
    )
    # And submit a regularization so the queue spans two types.
    await client.post(
        "/api/v1/attendance/regularize",
        headers=_h(emp),
        json={
            "date": "2026-04-20",
            "requested_check_in": "2026-04-20T09:00:00",
            "requested_check_out": "2026-04-20T18:00:00",
            "reason": "Forgot to mark",
        },
    )

    hr = await _login(client, "hr@hrms.com", "hr123")
    counts = (
        await client.get("/api/v1/approvals/inbox/counts", headers=_h(hr))
    ).json()
    by_type = {c["request_type"]: c["count"] for c in counts}
    assert by_type.get("leave_request", 0) >= 1
    assert by_type.get("attendance_regularization", 0) >= 1


@pytest.mark.asyncio
async def test_employee_cannot_act_on_approvals(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/approvals/inbox", headers=_h(emp))
    assert r.status_code == 403

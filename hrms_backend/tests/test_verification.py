"""Phase 11 verification tests."""
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
async def test_seeded_templates_and_queue(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    templates = (
        await client.get("/api/v1/verification/templates", headers=_h(token))
    ).json()
    assert len(templates) == 3
    assert {t["code"] for t in templates} == {
        "VT-ADDRESS-V1",
        "VT-EMPLOY-V1",
        "VT-DOC-V1",
    }

    queue = (
        await client.get("/api/v1/verification/queue", headers=_h(token))
    ).json()
    assert len(queue) == 2
    assert {v["status"] for v in queue} == {"pending"}
    assert all(v["ticket_number"].startswith("JKT/V/") for v in queue)


@pytest.mark.asyncio
async def test_template_driven_required_field_validation(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    queue = (
        await client.get("/api/v1/verification/queue", headers=_h(token))
    ).json()
    addr_job = next(v for v in queue if v["type"] == "address")

    # Start it
    r = await client.post(
        f"/api/v1/verification/{addr_job['id']}/start", headers=_h(token)
    )
    assert r.status_code == 200, r.text

    # Submit without required field → 422
    r = await client.post(
        f"/api/v1/verification/{addr_job['id']}/submit",
        headers=_h(token),
        json={
            "form_data": {"person_met": "Anil"},  # missing relation, duration, etc
            "photos": ["https://example.com/front.jpg",
                       "https://example.com/nameplate.jpg"],
            "signature_url": "https://example.com/sig.png",
            "result": "positive",
        },
    )
    assert r.status_code == 422
    assert "required" in r.json()["detail"].lower()

    # Submit without photos → 422 (template requires them)
    r = await client.post(
        f"/api/v1/verification/{addr_job['id']}/submit",
        headers=_h(token),
        json={
            "form_data": {
                "person_met": "Anil Sharma",
                "relation": "parent",
                "duration_at_address": 5,
                "ownership": "owned",
                "address_type": "independent_house",
            },
            "signature_url": "https://example.com/sig.png",
            "result": "positive",
        },
    )
    assert r.status_code == 422

    # Submit without signature → 422 (template requires it)
    r = await client.post(
        f"/api/v1/verification/{addr_job['id']}/submit",
        headers=_h(token),
        json={
            "form_data": {
                "person_met": "Anil Sharma",
                "relation": "parent",
                "duration_at_address": 5,
                "ownership": "owned",
                "address_type": "independent_house",
            },
            "photos": ["https://example.com/front.jpg",
                       "https://example.com/nameplate.jpg"],
            "result": "positive",
        },
    )
    assert r.status_code == 422
    assert "signature" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_full_lifecycle_submit_and_audit(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    queue = (
        await client.get("/api/v1/verification/queue", headers=_h(token))
    ).json()
    addr_job = next(v for v in queue if v["type"] == "address")

    await client.post(
        f"/api/v1/verification/{addr_job['id']}/start", headers=_h(token)
    )
    r = await client.post(
        f"/api/v1/verification/{addr_job['id']}/submit",
        headers=_h(token),
        json={
            "form_data": {
                "person_met": "Anil Sharma",
                "relation": "parent",
                "duration_at_address": 6,
                "ownership": "owned",
                "address_type": "independent_house",
                "neighbour_remarks": "Stays here, well-known",
            },
            "photos": [
                "https://example.com/front.jpg",
                "https://example.com/nameplate.jpg",
            ],
            "signature_url": "https://example.com/sig.png",
            "geo_lat": 12.9081,
            "geo_lng": 77.5832,
            "result": "positive",
            "remarks": "All claims verified by parent",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "audit_pending"
    assert r.json()["geo_lat"] == "12.9081"

    # Audit queue should now contain it
    audit_q = (
        await client.get(
            "/api/v1/verification/audit-queue", headers=_h(hr_token)
        )
    ).json()
    assert any(v["id"] == addr_job["id"] for v in audit_q)

    # Approve audit
    r = await client.post(
        f"/api/v1/verification/{addr_job['id']}/audit",
        headers=_h(hr_token),
        json={"audit_status": "approved", "audit_comments": "Looks good"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"

    # Get the report PDF
    r = await client.get(
        f"/api/v1/verification/{addr_job['id']}/report", headers=_h(hr_token)
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_audit_rework_sends_back_to_in_progress(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    queue = (
        await client.get("/api/v1/verification/queue", headers=_h(token))
    ).json()
    emp_job = next(v for v in queue if v["type"] == "employment")

    await client.post(
        f"/api/v1/verification/{emp_job['id']}/start", headers=_h(token)
    )
    await client.post(
        f"/api/v1/verification/{emp_job['id']}/submit",
        headers=_h(token),
        json={
            "form_data": {
                "company_name": "Sunrise Logistics",
                "designation": "Operations Lead",
                "joining_date": "2022-04-01",
                "verifier_name": "Ms. Suman",
                "verifier_designation": "HR Manager",
            },
            "photos": ["https://example.com/signage.jpg"],
            "result": "partial",
        },
    )

    r = await client.post(
        f"/api/v1/verification/{emp_job['id']}/audit",
        headers=_h(hr_token),
        json={
            "audit_status": "rework",
            "audit_comments": "Get HR letter on letterhead",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"
    assert r.json()["submitted_at"] is None


@pytest.mark.asyncio
async def test_auditor_rejection_adds_fraud_flag(client):
    """A rejected audit should auto-create a suspicious_pattern flag."""
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    field_token = await _login(client, "jkt019@jaikalki.com", "Password@123")

    # Create a fresh verification via HR
    templates = (
        await client.get(
            "/api/v1/verification/templates", headers=_h(hr_token)
        )
    ).json()
    doc_template = next(t for t in templates if t["code"] == "VT-DOC-V1")

    # Need JKT019's id
    # Look up JKT019's employee id from the queue (already assigned to them)
    queue = (
        await client.get(
            "/api/v1/verification/queue", headers=_h(field_token)
        )
    ).json()
    field_emp_id = queue[0]["assigned_to"]

    r = await client.post(
        "/api/v1/verification/",
        headers=_h(hr_token),
        json={
            "template_id": doc_template["id"],
            "subject_name": "Test Subject",
            "subject_data": {"applicant_id": "TST-001"},
            "address": "Test address",
            "assigned_to": field_emp_id,
        },
    )
    assert r.status_code == 201, r.text
    vid = r.json()["id"]

    # Field employee submits
    await client.post(
        f"/api/v1/verification/{vid}/start", headers=_h(field_token)
    )
    await client.post(
        f"/api/v1/verification/{vid}/submit",
        headers=_h(field_token),
        json={
            "form_data": {
                "document_type": "pan",
                "document_number": "ABCDE1234F",
                "name_match": True,
                "tamper_check": True,
            },
            "photos": ["https://example.com/pan-front.jpg"],
            "result": "positive",
        },
    )

    # Auditor rejects
    r = await client.post(
        f"/api/v1/verification/{vid}/audit",
        headers=_h(hr_token),
        json={
            "audit_status": "rejected",
            "audit_comments": "Photo mismatched name",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "audit_failed"
    assert any(
        f["flag_type"] == "suspicious_pattern" for f in body["fraud_flags"]
    )


@pytest.mark.asyncio
async def test_duplicate_subject_auto_flag(client):
    """Creating a second verification with the same subject + type within 30 days
    should be auto-flagged."""
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    field_token = await _login(client, "jkt019@jaikalki.com", "Password@123")

    templates = (
        await client.get(
            "/api/v1/verification/templates", headers=_h(hr_token)
        )
    ).json()
    addr_template = next(t for t in templates if t["code"] == "VT-ADDRESS-V1")

    # Look up JKT019's employee id from the queue (already assigned to them)
    queue = (
        await client.get(
            "/api/v1/verification/queue", headers=_h(field_token)
        )
    ).json()
    field_emp_id = queue[0]["assigned_to"]

    # First verification (already seeded subject "Rohit Sharma" of type address)
    r = await client.post(
        "/api/v1/verification/",
        headers=_h(hr_token),
        json={
            "template_id": addr_template["id"],
            "subject_name": "Rohit Sharma",  # matches seed
            "subject_data": {"applicant_id": "DUP-001"},
            "assigned_to": field_emp_id,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    # Re-fetch to pick up the flag created post-commit
    r = await client.get(
        f"/api/v1/verification/{body['id']}", headers=_h(hr_token)
    )
    assert r.status_code == 200
    assert any(
        f["flag_type"] == "duplicate_subject" for f in r.json()["fraud_flags"]
    )


@pytest.mark.asyncio
async def test_tat_stats_endpoint(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/verification/tat-stats", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    assert {"total", "on_time", "breached", "avg_hours", "breach_pct"} <= set(
        body
    )

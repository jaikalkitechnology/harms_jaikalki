"""Phase 8 Justice Portal tests."""
import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Encryption round-trip (unit) ──────────────────────────────────────
def test_encryption_round_trip():
    from app.services import encryption

    plain = "Confidential statement with special chars 🔐"
    ct = encryption.encrypt(plain)
    assert ct.startswith("v1:")
    assert encryption.is_encrypted(ct) is True
    assert encryption.decrypt(ct) == plain


def test_encryption_handles_none_and_empty():
    from app.services import encryption

    assert encryption.encrypt(None) is None
    assert encryption.decrypt(None) is None
    assert encryption.encrypt("") == ""
    assert encryption.decrypt("") == ""


def test_decrypt_passthrough_on_legacy_plaintext():
    from app.services import encryption

    # No v1: prefix → return as-is.
    assert encryption.decrypt("legacy") == "legacy"


# ── Submit ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_employee_submits_general_complaint(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/justice/submit",
        headers=_h(token),
        json={
            "complaint_type": "general",
            "privacy_level": "open",
            "severity": "low",
            "subject": "Office WiFi keeps dropping",
            "description": "Every afternoon the WiFi drops for ~10 minutes.",
            "desired_outcome": "Stable connectivity",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ticket_number"].startswith("JKT/JC/")
    assert body["status"] == "submitted"
    assert body["description"] == "Every afternoon the WiFi drops for ~10 minutes."


@pytest.mark.asyncio
async def test_anonymous_complaint_drops_employee_link(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/justice/submit",
        headers=_h(token),
        json={
            "complaint_type": "fraud",
            "privacy_level": "anonymous",
            "severity": "high",
            "subject": "Procurement irregularity",
            "description": "Saw vendor invoices rerouted to a personal account.",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["complainant_employee_id"] is None
    assert body["privacy_level"] == "anonymous"


@pytest.mark.asyncio
async def test_posh_complaint_sets_90_day_deadline(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/justice/submit",
        headers=_h(token),
        json={
            "complaint_type": "sexual_harassment",
            "privacy_level": "confidential",
            "severity": "high",
            "subject": "Inappropriate behaviour from senior",
            "description": "Repeated unwelcome remarks in 1:1 meetings.",
            "accused": [{"name": "Mr. X"}],
        },
    )
    assert r.status_code == 201
    assert r.json()["deadline_at"] is not None


# ── Access boundaries ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_employee_cannot_view_authority_inbox(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/justice/inbox", headers=_h(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_director_sees_all_complaints_in_inbox(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    # Submit a couple of complaints
    for ct in ("general", "manager_issue", "fraud"):
        await client.post(
            "/api/v1/justice/submit",
            headers=_h(emp),
            json={
                "complaint_type": ct,
                "privacy_level": "confidential",
                "severity": "low",
                "subject": f"Subject for {ct}",
                "description": "Details about the complaint.",
            },
        )

    director = await _login(client, "admin@hrms.com", "admin123")
    inbox = (
        await client.get("/api/v1/justice/inbox", headers=_h(director))
    ).json()
    types = {c["complaint_type"] for c in inbox}
    assert {"general", "manager_issue", "fraud"} & types == {
        "general", "manager_issue", "fraud",
    }


@pytest.mark.asyncio
async def test_hr_cannot_see_director_issue_complaints(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/justice/submit",
        headers=_h(emp),
        json={
            "complaint_type": "director_issue",
            "privacy_level": "confidential",
            "severity": "high",
            "subject": "Concern about Director conduct",
            "description": "Detailed account here.",
        },
    )
    cid = r.json()["id"]

    hr = await _login(client, "hr@hrms.com", "hr123")
    fetch = await client.get(f"/api/v1/justice/{cid}", headers=_h(hr))
    assert fetch.status_code == 403


# ── Audit log ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_view_records_audit_log(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/justice/submit",
        headers=_h(emp),
        json={
            "complaint_type": "general",
            "privacy_level": "confidential",
            "severity": "low",
            "subject": "Audit log test",
            "description": "Description.",
        },
    )
    cid = r.json()["id"]

    director = await _login(client, "admin@hrms.com", "admin123")
    detail = (
        await client.get(f"/api/v1/justice/{cid}", headers=_h(director))
    ).json()
    actions = [entry["action"] for entry in detail["access_log"]]
    assert "submit" in actions
    assert "view" in actions


# ── Action workflow ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_assign_then_resolve_flow(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/justice/submit",
        headers=_h(emp),
        json={
            "complaint_type": "manager_issue",
            "privacy_level": "confidential",
            "severity": "medium",
            "subject": "Manager favouritism",
            "description": "Detailed account.",
        },
    )
    cid = r.json()["id"]

    hr = await _login(client, "hr@hrms.com", "hr123")
    assign = await client.post(
        f"/api/v1/justice/{cid}/assign",
        headers=_h(hr),
        json={"user_id": 3},  # any valid user id from seed
    )
    assert assign.status_code == 200
    assert assign.json()["status"] == "under_investigation"

    action = await client.post(
        f"/api/v1/justice/{cid}/action",
        headers=_h(hr),
        json={"action_type": "warning_issued", "notes": "Verbal warning issued"},
    )
    assert action.status_code == 201
    assert action.json()["notes"] == "Verbal warning issued"

    resolve = await client.post(
        f"/api/v1/justice/{cid}/resolve",
        headers=_h(hr),
        json={"notes": "Issue addressed", "action_type": "case_closed"},
    )
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "resolved"


# ── ICC compliance ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_icc_compliance_status_satisfied_after_seed(client):
    director = await _login(client, "admin@hrms.com", "admin123")
    r = await client.get("/api/v1/justice/icc/compliance", headers=_h(director))
    assert r.status_code == 200
    body = r.json()
    assert body["compliant"] is True, body["reasons"]
    assert body["member_count"] >= 4
    assert body["women_count"] * 2 >= body["member_count"]
    assert body["external_count"] >= 1
    assert body["has_presiding_officer"] is True


# ── POSH annual report ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_posh_annual_report_aggregates(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    await client.post(
        "/api/v1/justice/submit",
        headers=_h(emp),
        json={
            "complaint_type": "sexual_harassment",
            "privacy_level": "confidential",
            "severity": "high",
            "subject": "Annual report aggregation",
            "description": "Details.",
        },
    )
    director = await _login(client, "admin@hrms.com", "admin123")
    from datetime import date

    report = await client.get(
        f"/api/v1/justice/posh/annual-report?year={date.today().year}",
        headers=_h(director),
    )
    assert report.status_code == 200
    body = report.json()
    assert body["total_complaints"] >= 1


# ── Resources ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_resources_endpoint_open_to_all(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/justice/resources", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    numbers = {h["number"] for h in body["helplines"]}
    assert "1091" in numbers
    assert "100" in numbers

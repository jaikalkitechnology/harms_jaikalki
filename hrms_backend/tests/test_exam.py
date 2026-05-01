"""Phase 13 examination system tests."""
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
async def test_seeded_exam_visible_to_employees(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    exams = (await client.get("/api/v1/exams/", headers=_h(token))).json()
    assert len(exams) >= 1
    posh = next(e for e in exams if e["code"] == "JKT-EXAM-POSH-2026")
    assert posh["exam_type"] == "certification"
    assert posh["passing_percentage"] == 70
    assert posh["is_published"] is True


@pytest.mark.asyncio
async def test_full_attempt_lifecycle_pass_issues_certificate(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    exams = (await client.get("/api/v1/exams/", headers=_h(token))).json()
    exam = next(e for e in exams if e["code"] == "JKT-EXAM-POSH-2026")

    # Start
    r = await client.post(
        f"/api/v1/exams/{exam['id']}/start", headers=_h(token)
    )
    assert r.status_code == 200, r.text
    body = r.json()
    attempt_id = body["attempt_id"]
    assert body["time_limit_minutes"] == 10
    questions = body["questions"]
    assert len(questions) >= 1
    # Public view must not leak is_correct
    assert all(
        "is_correct" not in o
        for q in questions
        for o in q["options"]
    )

    # Read the full questions (with correctness) via the question bank
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    bank = (
        await client.get("/api/v1/exams/questions", headers=_h(hr_token))
    ).json()
    by_id = {q["id"]: q for q in bank}

    # Build correct answers for each candidate question
    answers = []
    for q in questions:
        full = by_id[q["id"]]
        if q["question_type"] in ("single_choice", "true_false"):
            correct = next(
                o for o in full["options"] if o["is_correct"]
            )
            answers.append(
                {
                    "question_id": q["id"],
                    "selected_option_ids": [correct["id"]],
                    "time_taken_seconds": 8,
                }
            )
        else:  # multiple_choice
            correct_ids = [
                o["id"] for o in full["options"] if o["is_correct"]
            ]
            answers.append(
                {
                    "question_id": q["id"],
                    "selected_option_ids": correct_ids,
                    "time_taken_seconds": 12,
                }
            )

    # Submit
    r = await client.post(
        f"/api/v1/exams/attempts/{attempt_id}/submit",
        headers=_h(token),
        json={"answers": answers, "cheating_flags": []},
    )
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["status"] == "submitted"
    assert result["passed"] is True
    assert float(result["percentage"]) == 100.0

    # Certificate should now exist
    certs = (
        await client.get(
            "/api/v1/exams/me/certificates", headers=_h(token)
        )
    ).json()
    assert len(certs) == 1
    cert = certs[0]
    assert cert["certificate_number"].startswith("JKT/CERT/")
    assert cert["title"] == "POSH Certification Exam 2026"

    # Verify endpoint
    r = await client.get(
        f"/api/v1/exams/certificates/verify/{cert['certificate_number']}",
        headers=_h(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["employee_name"] == "Employee Demo"

    # PDF download
    r = await client.get(
        f"/api/v1/exams/certificates/{cert['id']}/pdf",
        headers=_h(token),
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_failed_attempt_does_not_issue_certificate(client):
    token = await _login(client, "manager@hrms.com", "manager123")
    exams = (await client.get("/api/v1/exams/", headers=_h(token))).json()
    exam = next(e for e in exams if e["code"] == "JKT-EXAM-POSH-2026")

    r = await client.post(
        f"/api/v1/exams/{exam['id']}/start", headers=_h(token)
    )
    body = r.json()
    attempt_id = body["attempt_id"]

    # Submit nothing → 0%
    r = await client.post(
        f"/api/v1/exams/attempts/{attempt_id}/submit",
        headers=_h(token),
        json={"answers": [], "cheating_flags": []},
    )
    assert r.status_code == 200
    result = r.json()
    assert result["passed"] is False
    assert float(result["percentage"]) == 0.0

    certs = (
        await client.get(
            "/api/v1/exams/me/certificates", headers=_h(token)
        )
    ).json()
    assert certs == []


@pytest.mark.asyncio
async def test_resume_in_progress_attempt(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    exams = (await client.get("/api/v1/exams/", headers=_h(token))).json()
    exam = next(e for e in exams if e["code"] == "JKT-EXAM-POSH-2026")

    r1 = await client.post(
        f"/api/v1/exams/{exam['id']}/start", headers=_h(token)
    )
    aid_1 = r1.json()["attempt_id"]

    # Re-starting before submission should resume the same attempt
    r2 = await client.post(
        f"/api/v1/exams/{exam['id']}/start", headers=_h(token)
    )
    assert r2.json()["attempt_id"] == aid_1


@pytest.mark.asyncio
async def test_cheating_flags_invalidate_attempt_after_threshold(client):
    token = await _login(client, "admin2@hrms.com", "admin123")
    exams = (await client.get("/api/v1/exams/", headers=_h(token))).json()
    exam = next(e for e in exams if e["code"] == "JKT-EXAM-POSH-2026")

    r = await client.post(
        f"/api/v1/exams/{exam['id']}/start", headers=_h(token)
    )
    attempt_id = r.json()["attempt_id"]

    last_response = None
    for i in range(5):
        last_response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/flag",
            headers=_h(token),
            json={"flag_type": "tab_switch"},
        )
    body = last_response.json()
    assert body["flag_count"] == 5
    assert body["status"] == "invalidated"

    # Cannot submit an invalidated attempt
    r = await client.post(
        f"/api/v1/exams/attempts/{attempt_id}/submit",
        headers=_h(token),
        json={"answers": [], "cheating_flags": []},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_question_and_exam_lifecycle(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")

    # Create a question
    r = await client.post(
        "/api/v1/exams/questions",
        headers=_h(hr_token),
        json={
            "question_text": "What is 2 + 2?",
            "question_type": "single_choice",
            "topic": "Math",
            "difficulty": "easy",
            "marks": 1,
            "time_seconds": 20,
            "options": [
                {"option_text": "3", "is_correct": False, "sort_order": 0},
                {"option_text": "4", "is_correct": True, "sort_order": 1},
                {"option_text": "5", "is_correct": False, "sort_order": 2},
            ],
        },
    )
    assert r.status_code == 201, r.text
    qid = r.json()["id"]

    # Create an exam in draft (no questions → cannot publish)
    r = await client.post(
        "/api/v1/exams/",
        headers=_h(hr_token),
        json={
            "code": "TEST-MATH-1",
            "title": "Math basics",
            "exam_type": "practice",
            "total_questions": 1,
            "time_limit_minutes": 5,
            "passing_percentage": 50,
            "attempts_allowed": 5,
            "cooldown_hours": 0,
            "question_ids": [qid],
        },
    )
    assert r.status_code == 201
    eid = r.json()["id"]
    assert r.json()["is_published"] is False

    # Publish
    r = await client.post(
        f"/api/v1/exams/{eid}/publish",
        headers=_h(hr_token),
        json={"is_published": True},
    )
    assert r.status_code == 200
    assert r.json()["is_published"] is True


@pytest.mark.asyncio
async def test_question_creation_requires_correct_option(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/exams/questions",
        headers=_h(hr_token),
        json={
            "question_text": "No correct option?",
            "question_type": "single_choice",
            "marks": 1,
            "options": [
                {"option_text": "A", "is_correct": False, "sort_order": 0},
                {"option_text": "B", "is_correct": False, "sort_order": 1},
            ],
        },
    )
    assert r.status_code == 422
    assert "correct" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_unknown_certificate_returns_invalid(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get(
        "/api/v1/exams/certificates/verify/JKT/CERT/9999/DEADBEEF",
        headers=_h(token),
    )
    # Path with slashes is collapsed; use a flat number
    assert r.status_code in (200, 404)
    r = await client.get(
        "/api/v1/exams/certificates/verify/UNKNOWN-CERT-NUMBER",
        headers=_h(token),
    )
    assert r.status_code == 200
    assert r.json()["valid"] is False

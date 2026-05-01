"""Phase 12 LMS tests."""
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
async def test_seeded_catalog(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    courses = (
        await client.get("/api/v1/lms/courses", headers=_h(token))
    ).json()
    assert len(courses) == 3
    codes = {c["code"] for c in courses}
    assert codes == {
        "JKT-LMS-ONB-101",
        "JKT-LMS-POSH-2026",
        "JKT-LMS-FIELD-101",
    }

    mandatory = (
        await client.get("/api/v1/lms/courses/mandatory", headers=_h(token))
    ).json()
    assert len(mandatory) == 2  # ONB + POSH
    assert {c["code"] for c in mandatory} == {
        "JKT-LMS-ONB-101",
        "JKT-LMS-POSH-2026",
    }


@pytest.mark.asyncio
async def test_course_detail_returns_modules_and_lessons(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    courses = (
        await client.get("/api/v1/lms/courses", headers=_h(token))
    ).json()
    onboarding = next(c for c in courses if c["code"] == "JKT-LMS-ONB-101")
    r = await client.get(
        f"/api/v1/lms/courses/{onboarding['id']}", headers=_h(token)
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["modules"]) == 2
    assert all(len(m["lessons"]) > 0 for m in body["modules"])


@pytest.mark.asyncio
async def test_enroll_and_complete_lesson_drives_progress(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    courses = (
        await client.get("/api/v1/lms/courses", headers=_h(token))
    ).json()
    course = next(c for c in courses if c["code"] == "JKT-LMS-ONB-101")
    detail = (
        await client.get(
            f"/api/v1/lms/courses/{course['id']}", headers=_h(token)
        )
    ).json()
    lessons = [l for m in detail["modules"] for l in m["lessons"]]
    total = len(lessons)

    # Enrol
    r = await client.post(
        f"/api/v1/lms/courses/{course['id']}/enroll", headers=_h(token)
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "enrolled"
    assert r.json()["progress_percentage"] == 0

    # Complete first lesson
    first = lessons[0]
    r = await client.post(
        f"/api/v1/lms/lessons/{first['id']}/complete",
        headers=_h(token),
        json={"time_spent_seconds": 120},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "in_progress"
    expected_pct = int(100 / total)
    assert body["progress_percentage"] == expected_pct

    # Complete remaining
    for l in lessons[1:]:
        r = await client.post(
            f"/api/v1/lms/lessons/{l['id']}/complete",
            headers=_h(token),
            json={"time_spent_seconds": 60},
        )
        assert r.status_code == 200

    # Re-fetch enrolment via my-courses
    enrolments = (
        await client.get("/api/v1/lms/my-courses", headers=_h(token))
    ).json()
    onboarding = next(e for e in enrolments if e["course_id"] == course["id"])
    assert onboarding["status"] == "completed"
    assert onboarding["progress_percentage"] == 100


@pytest.mark.asyncio
async def test_complete_lesson_without_enrol_blocked(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    # Pick a lesson from FIELD course (employee not auto-enrolled)
    courses = (
        await client.get("/api/v1/lms/courses", headers=_h(token))
    ).json()
    field = next(c for c in courses if c["code"] == "JKT-LMS-FIELD-101")
    detail = (
        await client.get(
            f"/api/v1/lms/courses/{field['id']}", headers=_h(token)
        )
    ).json()
    lesson_id = detail["modules"][0]["lessons"][0]["id"]
    r = await client.post(
        f"/api/v1/lms/lessons/{lesson_id}/complete",
        headers=_h(token),
        json={"time_spent_seconds": 0},
    )
    assert r.status_code == 422
    assert "enrol" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_gamification_awards_points_and_badge(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    courses = (
        await client.get("/api/v1/lms/courses", headers=_h(token))
    ).json()
    onb = next(c for c in courses if c["code"] == "JKT-LMS-ONB-101")
    await client.post(
        f"/api/v1/lms/courses/{onb['id']}/enroll", headers=_h(token)
    )
    detail = (
        await client.get(
            f"/api/v1/lms/courses/{onb['id']}", headers=_h(token)
        )
    ).json()
    lessons = [l for m in detail["modules"] for l in m["lessons"]]
    for l in lessons:
        await client.post(
            f"/api/v1/lms/lessons/{l['id']}/complete",
            headers=_h(token),
            json={"time_spent_seconds": 60},
        )

    stats = (
        await client.get("/api/v1/lms/stats/me", headers=_h(token))
    ).json()
    assert stats["lessons_completed"] == len(lessons)
    assert stats["courses_completed"] == 1
    # Lesson points: 2+2+3+1 = 8 + course completion bonus (50) = 58
    assert stats["points"] >= 50
    assert stats["streak_days"] >= 1
    # Should have FIRST-LESSON badge at minimum
    badge_codes = {b["code"] for b in stats["badges"]}
    assert "FIRST-LESSON" in badge_codes
    # Onboarded requires courses_completed >= 1 and points >= 50 → satisfied
    assert "ONBOARDED" in badge_codes


@pytest.mark.asyncio
async def test_compliance_status_for_self(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/lms/compliance/me", headers=_h(token))
    assert r.status_code == 200
    body = r.json()
    # Two mandatory courses are seeded
    assert len(body) == 2
    assert all(c["status"] == "not_enrolled" for c in body)


@pytest.mark.asyncio
async def test_admin_create_and_publish_course(client):
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/lms/courses",
        headers=_h(hr_token),
        json={
            "code": "JKT-LMS-TEST-1",
            "title": "Test course",
            "description": "Just for tests",
            "category": "technical",
            "estimated_hours": 1,
            "points": 5,
            "modules": [
                {
                    "title": "Module 1",
                    "sort_order": 0,
                    "lessons": [
                        {
                            "title": "Welcome",
                            "content_type": "article",
                            "article_body": "Hi",
                            "duration_minutes": 5,
                            "sort_order": 0,
                            "points": 1,
                        }
                    ],
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    course = r.json()
    assert course["is_published"] is False

    # Publish it
    r = await client.post(
        f"/api/v1/lms/courses/{course['id']}/publish",
        headers=_h(hr_token),
        json={"is_published": True},
    )
    assert r.status_code == 200
    assert r.json()["is_published"] is True


@pytest.mark.asyncio
async def test_leaderboard_returns_entries(client):
    """After at least one employee earns points, leaderboard should be non-empty."""
    token = await _login(client, "employee@hrms.com", "employee123")
    # Earn a point first
    courses = (
        await client.get("/api/v1/lms/courses", headers=_h(token))
    ).json()
    onb = next(c for c in courses if c["code"] == "JKT-LMS-ONB-101")
    await client.post(
        f"/api/v1/lms/courses/{onb['id']}/enroll", headers=_h(token)
    )
    detail = (
        await client.get(
            f"/api/v1/lms/courses/{onb['id']}", headers=_h(token)
        )
    ).json()
    first_lesson = detail["modules"][0]["lessons"][0]
    await client.post(
        f"/api/v1/lms/lessons/{first_lesson['id']}/complete",
        headers=_h(token),
        json={"time_spent_seconds": 30},
    )

    r = await client.get("/api/v1/lms/leaderboard", headers=_h(token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert rows[0]["points"] >= 1

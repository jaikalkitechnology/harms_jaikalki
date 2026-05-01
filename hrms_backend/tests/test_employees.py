"""Phase 2 acceptance tests."""
from __future__ import annotations

from decimal import Decimal

import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Salary calculator (the headline contract) ────────────────────────
def test_salary_calc_matches_pooja_offer_letter():
    """Direct unit test against the calculator, no HTTP."""
    from decimal import Decimal as D
    from app.services.salary_calculator import JaikalkiSalaryCalculator

    class T:
        template_code = "JKT-TRAINEE-L1"
        template_name = "Junior Developer (Trainee L1)"
        category = "trainee"
        basic_amount = D("15000")
        hra_amount = D("4500")
        other_allowance = D("450")
        special_allowance = D("0")
        conveyance = D("0")
        medical_allowance = D("0")
        lta = D("0")
        food_coupon = D("0")
        travel_expense_max = D("0")
        is_paid_internship = False

    breakup = JaikalkiSalaryCalculator().calculate(T()).as_dict()
    assert breakup["basic"] == 15000
    assert breakup["hra"] == 4500
    assert breakup["other_allowance"] == 450
    assert breakup["gross"] == 19950
    assert breakup["pf_employee"] == 1800
    assert breakup["esic_employee"] == 150
    assert breakup["professional_tax"] == 0
    assert breakup["total_deductions"] == 1950
    assert breakup["net_salary"] == 18000
    assert breakup["pf_employer"] == 1950
    assert breakup["esic_employer"] == 649
    assert breakup["total_ctc_monthly"] == 22549
    assert breakup["total_ctc_annual"] == 270588


def test_salary_calc_intern_template_returns_only_travel_expense():
    from decimal import Decimal as D
    from app.services.salary_calculator import JaikalkiSalaryCalculator

    class T:
        template_code = "JKT-INTERN-001"
        template_name = "Intern (Travel Only)"
        category = "intern"
        basic_amount = D("0")
        hra_amount = D("0")
        other_allowance = D("0")
        special_allowance = D("0")
        conveyance = D("0")
        medical_allowance = D("0")
        lta = D("0")
        food_coupon = D("0")
        travel_expense_max = D("3000")
        is_paid_internship = False

    breakup = JaikalkiSalaryCalculator().calculate(T()).as_dict()
    assert breakup["is_intern"] is True
    assert breakup["gross"] == 0
    assert breakup["pf_employee"] == 0
    assert breakup["travel_expense_max"] == 3000


# ── HTTP: scoping ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_director_sees_all_employees(client):
    token = await _login(client, "admin@hrms.com", "admin123")
    r = await client.get("/api/v1/employees", headers=_auth(token))
    assert r.status_code == 200
    codes = [e["employee_code"] for e in r.json()]
    assert "JKT001" in codes
    assert "JKT014" in codes
    assert "JKT017" in codes  # intern


@pytest.mark.asyncio
async def test_hr_sees_all_employees(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/employees", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 5


@pytest.mark.asyncio
async def test_manager_sees_only_their_team(client):
    token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/employees", headers=_auth(token))
    assert r.status_code == 200
    codes = {e["employee_code"] for e in r.json()}
    # Manager (JKT016) should see themselves + direct reports (JKT017 intern,
    # JKT018 employee). Should NOT see JKT001 (director) or JKT015 (HR).
    assert "JKT016" in codes
    assert "JKT001" not in codes
    assert "JKT015" not in codes


@pytest.mark.asyncio
async def test_employee_sees_only_self(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/employees", headers=_auth(token))
    assert r.status_code == 200
    codes = {e["employee_code"] for e in r.json()}
    assert codes == {"JKT018"}


@pytest.mark.asyncio
async def test_employee_me_returns_self(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/employees/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["employee_code"] == "JKT018"


# ── HTTP: salary template + calculator ────────────────────────────────
@pytest.mark.asyncio
async def test_salary_template_calculate_endpoint_for_pooja(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    # List templates and pick the trainee one.
    r = await client.get("/api/v1/salary-templates", headers=_auth(token))
    assert r.status_code == 200
    templates = r.json()
    trainee = next(t for t in templates if t["template_code"] == "JKT-TRAINEE-L1")

    r = await client.get(
        f"/api/v1/salary-templates/{trainee['id']}/calculate?ctc=270588",
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["gross"] == 19950
    assert body["net_salary"] == 18000
    assert body["total_ctc_annual"] == 270588


# ── HTTP: create employee with scoping & probation ────────────────────
@pytest.mark.asyncio
async def test_create_intern_no_salary_only_travel(client):
    token = await _login(client, "hr@hrms.com", "hr123")

    cats = (await client.get("/api/v1/employee-categories", headers=_auth(token))).json()
    intern_cat = next(c for c in cats if c["code"] == "INTERN")
    templates = (await client.get("/api/v1/salary-templates", headers=_auth(token))).json()
    intern_tpl = next(t for t in templates if t["template_code"] == "JKT-INTERN-001")

    r = await client.post(
        "/api/v1/employees",
        headers=_auth(token),
        json={
            "first_name": "Brand",
            "last_name": "NewIntern",
            "category_id": intern_cat["id"],
            "salary_template_id": intern_tpl["id"],
            "date_of_joining": "2026-05-15",
        },
    )
    assert r.status_code == 201, r.text
    emp = r.json()
    assert emp["employee_code"].startswith("JKT")
    assert emp["is_on_probation"] is False  # interns have no probation
    assert float(emp["ctc_annual"]) == 0


@pytest.mark.asyncio
async def test_create_trainee_sets_six_month_probation(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    cats = (await client.get("/api/v1/employee-categories", headers=_auth(token))).json()
    trainee = next(c for c in cats if c["code"] == "TRAINEE")
    templates = (await client.get("/api/v1/salary-templates", headers=_auth(token))).json()
    tpl = next(t for t in templates if t["template_code"] == "JKT-TRAINEE-L1")

    r = await client.post(
        "/api/v1/employees",
        headers=_auth(token),
        json={
            "first_name": "Brand",
            "last_name": "NewTrainee",
            "category_id": trainee["id"],
            "salary_template_id": tpl["id"],
            "ctc_annual": 270588,
            "date_of_joining": "2026-05-01",
        },
    )
    assert r.status_code == 201, r.text
    emp = r.json()
    assert emp["is_on_probation"] is True
    assert emp["probation_end_date"] is not None


@pytest.mark.asyncio
async def test_intern_cannot_have_ctc(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    cats = (await client.get("/api/v1/employee-categories", headers=_auth(token))).json()
    intern_cat = next(c for c in cats if c["code"] == "INTERN")

    r = await client.post(
        "/api/v1/employees",
        headers=_auth(token),
        json={
            "first_name": "Bad",
            "last_name": "Intern",
            "category_id": intern_cat["id"],
            "ctc_annual": 100000,
            "date_of_joining": "2026-05-15",
        },
    )
    assert r.status_code == 422


# ── Probation extension + confirmation ────────────────────────────────
@pytest.mark.asyncio
async def test_extend_probation_then_confirm(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    # JKT014 Pooja is on probation in the seed.
    employees = (
        await client.get("/api/v1/employees?search=Pooja", headers=_auth(token))
    ).json()
    pooja = next(e for e in employees if e["employee_code"] == "JKT014")

    r = await client.post(
        f"/api/v1/employees/{pooja['id']}/extend-probation",
        headers=_auth(token),
        json={"months": 2, "reason": "Performance review pending"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "extended"
    assert r.json()["is_extended"] is True

    r = await client.post(
        f"/api/v1/employees/{pooja['id']}/confirm",
        headers=_auth(token),
        json={"confirmation_letter_url": None},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "confirmed"

    detail = (
        await client.get(
            f"/api/v1/employees/{pooja['id']}", headers=_auth(token)
        )
    ).json()
    assert detail["is_on_probation"] is False
    assert detail["confirmation_date"] is not None


@pytest.mark.asyncio
async def test_expiring_probations_lists_pooja(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get(
        "/api/v1/employees/probation/expiring?days=365", headers=_auth(token)
    )
    assert r.status_code == 200
    codes = [item["employee_code"] for item in r.json()]
    assert "JKT014" in codes


# ── Intern travel expense ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_intern_can_submit_and_hr_can_approve_expense(client):
    intern_token = await _login(client, "jkt017@jaikalki.com", "changeme123")
    r = await client.post(
        "/api/v1/interns/expenses",
        headers=_auth(intern_token),
        json={
            "expense_date": "2026-05-02",
            "expense_type": "office_commute",
            "amount": 150,
            "description": "Local train Mira Road to office",
        },
    )
    assert r.status_code == 201, r.text
    expense = r.json()
    assert expense["status"] == "pending"
    expense_id = expense["id"]

    # Non-intern cannot submit
    emp_token = await _login(client, "employee@hrms.com", "employee123")
    bad = await client.post(
        "/api/v1/interns/expenses",
        headers=_auth(emp_token),
        json={
            "expense_date": "2026-05-02",
            "expense_type": "office_commute",
            "amount": 100,
        },
    )
    assert bad.status_code == 403

    # HR sees pending list and approves
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    pending = (
        await client.get("/api/v1/interns/expenses/pending", headers=_auth(hr_token))
    ).json()
    assert any(e["id"] == expense_id for e in pending)

    r = await client.post(
        f"/api/v1/interns/expenses/{expense_id}/approve",
        headers=_auth(hr_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_intern_travel_amount_capped_by_template(client):
    intern_token = await _login(client, "jkt017@jaikalki.com", "changeme123")
    r = await client.post(
        "/api/v1/interns/expenses",
        headers=_auth(intern_token),
        json={
            "expense_date": "2026-05-02",
            "expense_type": "office_commute",
            "amount": 99999,  # way above 3000 cap
        },
    )
    assert r.status_code == 422


# ── Org chart ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_org_chart_returns_hierarchy(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.get("/api/v1/employees/org/chart", headers=_auth(token))
    assert r.status_code == 200
    forest = r.json()
    # Director should be a root and have at least one child (Manager).
    director = next((n for n in forest if n["employee_code"] == "JKT001"), None)
    assert director is not None
    child_codes = {c["employee_code"] for c in director["children"]}
    assert "JKT016" in child_codes  # Manager Demo reports to Director


# ── Dashboard summary ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_dashboard_me_employee_view(client):
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/dashboard/me", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "employee"
    assert body["employee_code"] == "JKT018"
    assert isinstance(body["leave_balances"], list)
    assert body["next_payday_in_days"] >= 0


@pytest.mark.asyncio
async def test_dashboard_me_manager_includes_team(client):
    token = await _login(client, "manager@hrms.com", "manager123")
    r = await client.get("/api/v1/dashboard/me", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "manager"
    assert body["team_size"] >= 1
    codes = [m["employee_code"] for m in body["team_today"]]
    assert "JKT017" in codes or "JKT018" in codes


@pytest.mark.asyncio
async def test_dashboard_me_director_includes_headcount(client):
    token = await _login(client, "admin@hrms.com", "admin123")
    r = await client.get("/api/v1/dashboard/me", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "director"
    assert body["total_headcount"] >= 5


# ── Lookups ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_departments_and_designations(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    depts = (await client.get("/api/v1/departments", headers=_auth(token))).json()
    assert any(d["code"] == "IT" for d in depts)
    desigs = (await client.get("/api/v1/designations", headers=_auth(token))).json()
    assert any(d["code"] == "DEV1" for d in desigs)

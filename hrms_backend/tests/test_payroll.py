"""Phase 7 payroll tests."""
import pytest


async def _login(client, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Payroll run end-to-end ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_run_payroll_creates_payslips(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/payroll/run",
        headers=_h(token),
        json={"year": 2026, "month": 5},
    )
    assert r.status_code == 201, r.text
    run = r.json()
    assert run["year"] == 2026
    assert run["month"] == 5
    assert run["status"] == "processed"
    # 5 salary-bearing employees in seed (intern excluded).
    assert run["total_employees"] >= 5

    detail = (
        await client.get(
            f"/api/v1/payroll/runs/{run['id']}", headers=_h(token)
        )
    ).json()
    assert len(detail["payslips"]) == run["total_employees"]


@pytest.mark.asyncio
async def test_pooja_payslip_matches_offer_letter(client):
    """Headline test: JKT014's monthly payslip = offer letter numbers."""
    token = await _login(client, "hr@hrms.com", "hr123")
    await client.post(
        "/api/v1/payroll/run",
        headers=_h(token),
        json={"year": 2026, "month": 6},
    )

    # Pooja's user (created in seed_employees).
    pooja = await _login(client, "pooja@jaikalki.com", "changeme123")
    payslips = (
        await client.get("/api/v1/payroll/payslips/me", headers=_h(pooja))
    ).json()
    assert payslips, "Pooja should have at least one payslip"
    # Pick the June 2026 one explicitly.
    p = next(p for p in payslips if p["year"] == 2026 and p["month"] == 6)
    assert int(float(p["basic"])) == 15000
    assert int(float(p["hra"])) == 4500
    assert int(float(p["other_allowance"])) == 450
    assert int(float(p["gross"])) == 19950
    assert int(float(p["pf_employee"])) == 1800
    assert int(float(p["esic_employee"])) == 150
    assert int(float(p["pf_employer"])) == 1950
    assert int(float(p["esic_employer"])) == 649
    # Net pay = gross - deductions (no LOP and no reimbursements)
    assert int(float(p["net_pay"])) == 18000


@pytest.mark.asyncio
async def test_finalize_locks_run(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    r = await client.post(
        "/api/v1/payroll/run",
        headers=_h(token),
        json={"year": 2026, "month": 7},
    )
    run_id = r.json()["id"]
    finalize = await client.post(
        f"/api/v1/payroll/runs/{run_id}/finalize", headers=_h(token)
    )
    assert finalize.status_code == 200
    assert finalize.json()["status"] == "finalized"

    # Re-running while finalized is rejected.
    again = await client.post(
        "/api/v1/payroll/run",
        headers=_h(token),
        json={"year": 2026, "month": 7},
    )
    assert again.status_code == 409


# ── Offer letter ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_offer_letter_generation_for_pooja(client):
    """Generate Pooja's offer letter — verifies the headline deliverable."""
    token = await _login(client, "hr@hrms.com", "hr123")

    # Look up Pooja's id.
    employees = (
        await client.get(
            "/api/v1/employees?search=Pooja", headers=_h(token)
        )
    ).json()
    pooja = next(e for e in employees if e["employee_code"] == "JKT014")

    # Generate (the post-handler).
    r = await client.post(
        f"/api/v1/payroll/offer-letter/{pooja['id']}", headers=_h(token)
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["doc_type"] == "offer_letter"
    assert body["letter_number"] is not None
    assert body["letter_number"].startswith("JKT/HR/AL/")
    assert body["letter_number"].endswith("/2026") or body["letter_number"].endswith(
        f"/{__import__('datetime').date.today().year}"
    )

    # Preview returns a real PDF.
    preview = await client.get(
        f"/api/v1/payroll/offer-letter/{pooja['id']}/preview",
        headers=_h(token),
    )
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "application/pdf"
    pdf_bytes = preview.content
    assert pdf_bytes.startswith(b"%PDF"), "Should be a valid PDF"
    # Pooja's name should appear somewhere in the PDF byte-stream.
    assert b"Pooja" in pdf_bytes


@pytest.mark.asyncio
async def test_offer_letter_sequence_increments(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    employees = (
        await client.get(
            "/api/v1/employees?search=Pooja", headers=_h(token)
        )
    ).json()
    pooja_id = next(e["id"] for e in employees if e["employee_code"] == "JKT014")

    first = (
        await client.post(
            f"/api/v1/payroll/offer-letter/{pooja_id}", headers=_h(token)
        )
    ).json()
    second = (
        await client.post(
            f"/api/v1/payroll/offer-letter/{pooja_id}", headers=_h(token)
        )
    ).json()
    # The numeric sequence in the middle should grow.
    seq_first = int(first["letter_number"].split("/")[-2])
    seq_second = int(second["letter_number"].split("/")[-2])
    assert seq_second > seq_first


# ── Confirmation letter ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_confirmation_letter_generates(client):
    token = await _login(client, "hr@hrms.com", "hr123")
    employees = (
        await client.get(
            "/api/v1/employees?search=Pooja", headers=_h(token)
        )
    ).json()
    pooja_id = next(e["id"] for e in employees if e["employee_code"] == "JKT014")

    r = await client.post(
        f"/api/v1/payroll/confirmation-letter/{pooja_id}",
        headers=_h(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["doc_type"] == "confirmation_letter"
    assert body["letter_number"].startswith("JKT/HR/CL/")


# ── Reimbursements ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_reimbursement_submit_approve_then_paid_in_payroll(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    r = await client.post(
        "/api/v1/payroll/reimbursements",
        headers=_h(emp),
        json={
            "category": "travel",
            "amount": "1500.00",
            "bill_date": "2026-08-10",
            "description": "Cab to client site",
        },
    )
    assert r.status_code == 201, r.text
    rb_id = r.json()["id"]

    hr = await _login(client, "hr@hrms.com", "hr123")
    pending = (
        await client.get(
            "/api/v1/payroll/reimbursements/pending", headers=_h(hr)
        )
    ).json()
    assert any(p["id"] == rb_id for p in pending)

    approve = await client.post(
        f"/api/v1/payroll/reimbursements/{rb_id}/approve", headers=_h(hr)
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    # Run payroll for Aug — reimbursement should be marked paid.
    run = await client.post(
        "/api/v1/payroll/run",
        headers=_h(hr),
        json={"year": 2026, "month": 8},
    )
    run_id = run.json()["id"]

    mine = (
        await client.get(
            "/api/v1/payroll/reimbursements/me", headers=_h(emp)
        )
    ).json()
    rb = next(r for r in mine if r["id"] == rb_id)
    assert rb["status"] == "paid"
    assert rb["paid_in_run_id"] == run_id


# ── Investment declaration ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_investment_declaration_create_and_update(client):
    emp = await _login(client, "employee@hrms.com", "employee123")
    create = await client.post(
        "/api/v1/payroll/declaration",
        headers=_h(emp),
        json={
            "fy": "2026-27",
            "regime": "new",
            "section_80c": "150000",
        },
    )
    assert create.status_code == 201, create.text
    assert float(create.json()["section_80c"]) == 150000

    # Update — same FY.
    update = await client.post(
        "/api/v1/payroll/declaration",
        headers=_h(emp),
        json={
            "fy": "2026-27",
            "regime": "old",
            "section_80c": "100000",
        },
    )
    assert update.status_code == 201
    assert update.json()["regime"] == "old"
    assert float(update.json()["section_80c"]) == 100000


# ── Direct PDF render unit test (no DB persistence) ───────────────────
def test_pooja_offer_letter_pdf_renders_offline():
    """Render directly from a fake template — sanity check the renderer."""
    from datetime import date as _date
    from decimal import Decimal as _D

    from app.services.jaikalki_documents import _render_offer_letter

    class _T:
        template_code = "JKT-TRAINEE-L1"
        template_name = "Junior Developer (Trainee L1)"
        category = "trainee"
        basic_amount = _D("15000")
        hra_amount = _D("4500")
        other_allowance = _D("450")
        special_allowance = _D("0")
        conveyance = _D("0")
        medical_allowance = _D("0")
        lta = _D("0")
        food_coupon = _D("0")
        travel_expense_max = _D("0")
        is_paid_internship = False
        has_probation = True
        probation_months = 6
        probation_extension_months = 2
        notice_period_probation = 15
        notice_period_confirmed = 30
        notice_period_termination = 7
        mediclaim_amount = _D("200000")
        pa_insurance_amount = _D("500000")

    class _Emp:
        id = 14
        employee_code = "JKT014"
        first_name = "Pooja"
        last_name = "Kumawat"
        gender = "female"
        personal_email = "pooja@example.com"
        date_of_joining = _date(2026, 4, 1)
        ctc_annual = _D("270588")
        salary_template = _T()
        designation = type("X", (), {"name": "Front-end Developer (Flutter)"})()
        department = type("X", (), {"name": "IT"})()
        category = type("X", (), {"name": "Trainee"})()
        work_location = "Mira Road, Thane"

    from app.services.salary_calculator import JaikalkiSalaryCalculator

    breakup = JaikalkiSalaryCalculator().calculate(_T()).as_dict()
    pdf = _render_offer_letter(
        _Emp(),
        letter_no="JKT/HR/AL/014/2026",
        on_date=_date(2026, 1, 1),
        breakup=breakup,
    )
    assert pdf.startswith(b"%PDF")
    assert b"Pooja" in pdf
    assert b"JKT014" in pdf

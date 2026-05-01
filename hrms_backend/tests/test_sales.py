"""Phase 10 sales tests."""
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
async def test_seeded_leads_and_products(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    leads = (
        await client.get("/api/v1/sales/leads?mine=true", headers=_h(token))
    ).json()
    assert len(leads) == 4
    stages = {l["stage"] for l in leads}
    assert stages == {"new", "contacted", "qualified", "proposal"}

    products = (
        await client.get("/api/v1/sales/products", headers=_h(token))
    ).json()
    assert len(products) == 5
    assert any(p["sku"] == "JKT-PROD-001" for p in products)


@pytest.mark.asyncio
async def test_pipeline_kanban_buckets(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    cols = (
        await client.get("/api/v1/sales/pipeline?mine=true", headers=_h(token))
    ).json()
    assert len(cols) == 7  # all stages
    by_stage = {c["stage"]: c for c in cols}
    assert by_stage["proposal"]["count"] == 1
    assert by_stage["qualified"]["count"] == 1
    assert float(by_stage["proposal"]["total_value"]) == 120000.00


@pytest.mark.asyncio
async def test_lead_stage_transition(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    leads = (
        await client.get("/api/v1/sales/leads?mine=true", headers=_h(token))
    ).json()
    new_lead = next(l for l in leads if l["stage"] == "new")

    r = await client.patch(
        f"/api/v1/sales/leads/{new_lead['id']}/stage",
        headers=_h(token),
        json={"stage": "qualified"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["stage"] == "qualified"
    assert r.json()["score"] == 50

    # Marking lost requires reason
    r = await client.patch(
        f"/api/v1/sales/leads/{new_lead['id']}/stage",
        headers=_h(token),
        json={"stage": "lost"},
    )
    assert r.status_code == 422

    r = await client.patch(
        f"/api/v1/sales/leads/{new_lead['id']}/stage",
        headers=_h(token),
        json={"stage": "lost", "lost_reason": "Budget"},
    )
    assert r.status_code == 200
    assert r.json()["stage"] == "lost"
    assert r.json()["lost_reason"] == "Budget"


@pytest.mark.asyncio
async def test_quote_create_totals_and_pdf(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    products = (
        await client.get("/api/v1/sales/products", headers=_h(token))
    ).json()
    customers = (
        await client.get("/api/v1/field/customers", headers=_h(token))
    ).json()
    p1 = next(p for p in products if p["sku"] == "JKT-PROD-001")
    p2 = next(p for p in products if p["sku"] == "JKT-PROD-002")

    r = await client.post(
        "/api/v1/sales/quotes",
        headers=_h(token),
        json={
            "customer_id": customers[0]["id"],
            "line_items": [
                {
                    "product_id": p1["id"],
                    "name": p1["name"],
                    "quantity": 1,
                    "unit_price": float(p1["unit_price"]),
                    "tax_pct": float(p1["tax_pct"]),
                },
                {
                    "product_id": p2["id"],
                    "name": p2["name"],
                    "quantity": 2,
                    "unit_price": float(p2["unit_price"]),
                    "tax_pct": float(p2["tax_pct"]),
                },
            ],
            "discount_pct": 10,
        },
    )
    assert r.status_code == 201, r.text
    q = r.json()
    # subtotal = 8499 + 18999*2 = 46497
    assert float(q["subtotal"]) == 46497.00
    # 10% discount = 4649.70
    assert float(q["discount_amount"]) == 4649.70
    assert float(q["total_amount"]) > 0
    assert q["status"] == "draft"
    assert q["quote_number"].startswith("JKT/Q/")

    # Fetch the PDF
    r = await client.get(
        f"/api/v1/sales/quotes/{q['id']}/pdf", headers=_h(token)
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_order_creates_and_delivered_updates_target(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    hr_token = await _login(client, "hr@hrms.com", "hr123")
    products = (
        await client.get("/api/v1/sales/products", headers=_h(token))
    ).json()
    customers = (
        await client.get("/api/v1/field/customers", headers=_h(token))
    ).json()
    p = next(p for p in products if p["sku"] == "JKT-PROD-001")

    r = await client.post(
        "/api/v1/sales/orders",
        headers=_h(token),
        json={
            "customer_id": customers[0]["id"],
            "line_items": [
                {
                    "product_id": p["id"],
                    "name": p["name"],
                    "quantity": 1,
                    "unit_price": float(p["unit_price"]),
                    "tax_pct": float(p["tax_pct"]),
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "pending"
    assert order["order_number"].startswith("JKT/SO/")

    # Mark delivered (HR has approval.act)
    r = await client.patch(
        f"/api/v1/sales/orders/{order['id']}/status",
        headers=_h(hr_token),
        json={"status": "delivered", "tracking_number": "TRK001"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "delivered"

    # Target should now reflect achievement
    r = await client.get("/api/v1/sales/targets/me", headers=_h(token))
    assert r.status_code == 200
    summary = r.json()
    assert summary is not None
    assert float(summary["target"]["achieved_amount"]) >= float(order["total_amount"]) - 0.01
    assert summary["achievement_pct"] > 0


@pytest.mark.asyncio
async def test_promotion_logging(client):
    token = await _login(client, "jkt019@jaikalki.com", "Password@123")
    r = await client.post(
        "/api/v1/sales/promotions",
        headers=_h(token),
        json={
            "event_name": "Bengaluru Trade Expo 2026",
            "location": "BIEC",
            "activity_date": "2026-05-01",
            "banners_placed": 3,
            "brochures_distributed": 250,
            "demos_given": 18,
            "leads_collected": 12,
            "notes": "High footfall on day 2",
        },
    )
    assert r.status_code == 201, r.text
    promo = r.json()
    assert promo["leads_collected"] == 12

    r = await client.get("/api/v1/sales/promotions/me", headers=_h(token))
    assert r.status_code == 200
    assert any(p["id"] == promo["id"] for p in r.json())


@pytest.mark.asyncio
async def test_target_summary_for_employee_without_target(client):
    # Employee@hrms.com has no sales target seeded → should return null
    token = await _login(client, "employee@hrms.com", "employee123")
    r = await client.get("/api/v1/sales/targets/me", headers=_h(token))
    assert r.status_code == 200
    assert r.json() is None

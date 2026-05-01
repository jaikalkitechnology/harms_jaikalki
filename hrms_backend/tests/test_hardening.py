"""Phase 18 hardening tests — security headers, rate limiting, health probes."""
import pytest


@pytest.mark.asyncio
async def test_security_headers_set_on_responses(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Referrer-Policy" in r.headers
    assert "Permissions-Policy" in r.headers
    # HSTS is only set in production — env defaults to "development" in tests
    assert "Strict-Transport-Security" not in r.headers


@pytest.mark.asyncio
async def test_request_id_header_propagates(client):
    r = await client.get("/", headers={"X-Request-ID": "abc-123"})
    assert r.headers.get("X-Request-ID") == "abc-123"
    assert "X-Response-Time-ms" in r.headers


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_threshold(client):
    """Hammer the login endpoint past the 20-rps window — expect 429s."""
    last = None
    payload = {"email": "nobody@example.com", "password": "wrong"}
    for _ in range(25):
        last = await client.post("/api/v1/auth/login", json=payload)
        if last.status_code == 429:
            break
    assert last.status_code == 429
    assert "retry-after" in {k.lower() for k in last.headers.keys()}
    body = last.json()
    assert body["code"] == "rate_limit_exceeded"


@pytest.mark.asyncio
async def test_health_live_probe(client):
    r = await client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_probe_local_storage(client):
    r = await client.get("/api/v1/health/ready")
    # DB + storage round-trips both succeed in tests; redis may be down
    # which results in `degraded`, also a valid 200.
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert body["checks"]["db"]["status"] == "ok"
    assert body["checks"]["storage"]["status"] == "ok"
    assert body["checks"]["storage"]["info"]["backend"] in ("local", "s3")

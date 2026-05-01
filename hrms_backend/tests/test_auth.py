import pytest


@pytest.mark.asyncio
async def test_mobile_login_success(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "employee@hrms.com", "password": "employee123"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_mobile_login_wrong_password(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "employee@hrms.com", "password": "nope"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_role_and_permissions(client):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "manager@hrms.com", "password": "manager123"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "manager"
    assert "leave.approve.team" in body["permissions"]
    assert body["user"]["email"] == "manager@hrms.com"


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "hr@hrms.com", "password": "hr123"},
    )
    refresh = login.json()["refresh_token"]

    r = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    assert new_refresh != refresh

    # Old refresh is now revoked.
    again = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "hr@hrms.com", "password": "hr123"},
    )
    refresh = login.json()["refresh_token"]

    out = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh}
    )
    assert out.status_code == 204

    again = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_sets_cookies(client):
    r = await client.post(
        "/api/admin/auth/login",
        json={"email": "super@jaikalki.com", "password": "super123"},
    )
    assert r.status_code == 200, r.text
    assert "jaikalki_access" in r.cookies
    assert "jaikalki_refresh" in r.cookies
    assert "jaikalki_csrf" in r.cookies
    body = r.json()
    assert body["role"] == "super_admin"


@pytest.mark.asyncio
async def test_admin_login_rejects_non_admin_account(client):
    r = await client.post(
        "/api/admin/auth/login",
        json={"email": "employee@hrms.com", "password": "employee123"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_me_via_cookie(client):
    await client.post(
        "/api/admin/auth/login",
        json={"email": "hr@hrms.com", "password": "hr123"},
    )
    r = await client.get("/api/admin/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["email"] == "hr@hrms.com"


@pytest.mark.asyncio
async def test_super_admin_can_list_permissions(client):
    await client.post(
        "/api/admin/auth/login",
        json={"email": "super@jaikalki.com", "password": "super123"},
    )
    r = await client.get("/api/admin/permissions")
    assert r.status_code == 200
    codes = [p["code"] for p in r.json()]
    assert "system.config" in codes
    assert "employee.view.all" in codes


@pytest.mark.asyncio
async def test_non_super_admin_cannot_list_permissions(client):
    await client.post(
        "/api/admin/auth/login",
        json={"email": "hr@hrms.com", "password": "hr123"},
    )
    r = await client.get("/api/admin/permissions")
    assert r.status_code == 403

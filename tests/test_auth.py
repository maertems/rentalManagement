import pytest
from httpx import AsyncClient

from tests.conftest import _seed_admin, ADMIN_EMAIL, ADMIN_PASSWORD

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_login_success(client: AsyncClient):
    await _seed_admin()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == ADMIN_EMAIL
    assert data["isAdmin"] == 1
    # Cookies were set
    assert "accessToken" in resp.cookies
    assert "refreshToken" in resp.cookies


async def test_login_wrong_password(client: AsyncClient):
    await _seed_admin()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_me_without_cookie_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_with_cookie_returns_user(authedClient: AsyncClient):
    resp = await authedClient.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == ADMIN_EMAIL


async def test_refresh_rotates_tokens(authedClient: AsyncClient):
    resp = await authedClient.post("/api/v1/auth/refresh")
    assert resp.status_code == 204
    # The client should still be authenticated afterwards
    me = await authedClient.get("/api/v1/auth/me")
    assert me.status_code == 200


async def test_logout_clears_cookies(authedClient: AsyncClient):
    resp = await authedClient.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    me = await authedClient.get("/api/v1/auth/me")
    assert me.status_code == 401

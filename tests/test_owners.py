import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_user(authedClient: AsyncClient, email: str = "owner_user@test.com") -> int:
    resp = await authedClient.post("/api/v1/users", json={
        "email": email,
        "password": "password123",
        "name": "Owner User",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_create_owner(authedClient: AsyncClient):
    user_id = await _create_user(authedClient, "create_owner@test.com")
    resp = await authedClient.post("/api/v1/owners", json={
        "name": "John Owner",
        "email": "john@owner.com",
        "city": "Paris",
        "zipCode": 75001,
        "userId": user_id,
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "John Owner"
    assert data["id"] is not None
    assert data["userId"] == user_id


async def test_create_owner_requires_user_id(authedClient: AsyncClient):
    resp = await authedClient.post("/api/v1/owners", json={"name": "No User"})
    assert resp.status_code == 422


async def test_create_owner_userId_unique(authedClient: AsyncClient):
    user_id = await _create_user(authedClient, "unique_owner@test.com")
    await authedClient.post("/api/v1/owners", json={"name": "First", "userId": user_id})
    resp = await authedClient.post("/api/v1/owners", json={"name": "Second", "userId": user_id})
    assert resp.status_code == 409


async def test_get_owner(authedClient: AsyncClient):
    user_id = await _create_user(authedClient, "get_owner@test.com")
    create = await authedClient.post("/api/v1/owners", json={"name": "Alice", "userId": user_id})
    id_ = create.json()["id"]
    resp = await authedClient.get(f"/api/v1/owners/{id_}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice"


async def test_get_owner_not_found(authedClient: AsyncClient):
    resp = await authedClient.get("/api/v1/owners/99999")
    assert resp.status_code == 404


async def test_list_owners(authedClient: AsyncClient):
    u1 = await _create_user(authedClient, "list_owner1@test.com")
    u2 = await _create_user(authedClient, "list_owner2@test.com")
    await authedClient.post("/api/v1/owners", json={"name": "Owner Lyon", "city": "Lyon", "userId": u1})
    await authedClient.post("/api/v1/owners", json={"name": "Owner Paris", "city": "Paris", "userId": u2})
    resp = await authedClient.get("/api/v1/owners?city=Lyon")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["city"] == "Lyon"
    assert resp.headers["x-total-count"] == "1"


async def test_update_owner(authedClient: AsyncClient):
    user_id = await _create_user(authedClient, "update_owner@test.com")
    create = await authedClient.post("/api/v1/owners", json={"name": "Old Name", "userId": user_id})
    id_ = create.json()["id"]
    resp = await authedClient.patch(f"/api/v1/owners/{id_}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


async def test_delete_owner(authedClient: AsyncClient):
    user_id = await _create_user(authedClient, "delete_owner@test.com")
    create = await authedClient.post("/api/v1/owners", json={"name": "To Delete", "userId": user_id})
    id_ = create.json()["id"]
    resp = await authedClient.delete(f"/api/v1/owners/{id_}")
    assert resp.status_code == 204
    get = await authedClient.get(f"/api/v1/owners/{id_}")
    assert get.status_code == 404


async def test_create_owner_full(authedClient: AsyncClient):
    resp = await authedClient.post("/api/v1/owners/full", json={
        "user": {"email": "full_owner@test.com", "password": "password123", "name": "Full Owner"},
        "owner": {"name": "Full Owner Corp", "city": "Lyon"},
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user"]["email"] == "full_owner@test.com"
    assert data["owner"]["name"] == "Full Owner Corp"
    assert data["owner"]["userId"] == data["user"]["id"]

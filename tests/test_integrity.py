import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_delete_place_with_places_units_returns_409(authedClient: AsyncClient):
    user = await authedClient.post("/api/v1/users", json={
        "email": "integrity_owner@test.com", "password": "password123"
    })
    owner = await authedClient.post("/api/v1/owners", json={
        "name": "Owner", "userId": user.json()["id"]
    })
    place = await authedClient.post("/api/v1/places", json={
        "name": "Place", "ownerId": owner.json()["id"]
    })
    place_id = place.json()["id"]
    await authedClient.post("/api/v1/placesUnits", json={
        "name": "Unit", "placeId": place_id
    })
    resp = await authedClient.delete(f"/api/v1/places/{place_id}")
    assert resp.status_code == 409


async def test_create_tenant_with_invalid_place_unit_returns_422(authedClient: AsyncClient):
    resp = await authedClient.post("/api/v1/tenants", json={
        "name": "Test Tenant",
        "withdrawDay": 5,
        "placeUnitId": 99999,
    })
    assert resp.status_code == 422


async def test_create_rent_receipt_with_invalid_tenant_returns_422(authedClient: AsyncClient):
    resp = await authedClient.post("/api/v1/rentReceipts", json={
        "tenantId": 99999,
        "amount": 800.0,
    })
    assert resp.status_code == 422


async def test_no_auth_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/owners")
    assert resp.status_code == 401

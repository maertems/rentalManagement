"""Tests for the aggregate endpoints: /places/full, /tenants/full, /tenants/{id}/receipts, /dashboard/occupancy."""
import pytest
from datetime import datetime
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _createPlaceWithUnits(authedClient: AsyncClient):
    user = await authedClient.post("/api/v1/users", json={
        "email": "place_owner@test.com",
        "password": "password123",
    })
    user_id = user.json()["id"]
    owner = await authedClient.post("/api/v1/owners", json={"name": "The Owner", "userId": user_id})
    owner_id = owner.json()["id"]
    resp = await authedClient.post(
        "/api/v1/places/full",
        json={
            "place": {
                "name": "Immeuble Test",
                "address": "10 rue du test",
                "city": "Paris",
                "zipCode": 75001,
                "ownerId": owner_id,
            },
            "units": [
                {
                    "name": "Appart 1",
                    "level": "1",
                    "flatshare": 0,
                    "surfaceArea": 45.0,
                    "rooms": [],
                },
                {
                    "name": "Appart 2",
                    "level": "2",
                    "flatshare": 1,
                    "surfaceArea": 80.0,
                    "rooms": [
                        {"name": "Chambre 1", "surfaceArea": 12.0},
                        {"name": "Chambre 2", "surfaceArea": 14.0},
                    ],
                },
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_place_full_with_units_and_rooms(authedClient: AsyncClient):
    data = await _createPlaceWithUnits(authedClient)
    assert data["place"]["name"] == "Immeuble Test"
    assert len(data["units"]) == 2
    unit1, unit2 = data["units"]
    assert unit1["name"] == "Appart 1"
    assert unit1["flatshare"] == 0
    assert unit1["rooms"] == []
    assert unit2["flatshare"] == 1
    assert len(unit2["rooms"]) == 2
    assert {r["name"] for r in unit2["rooms"]} == {"Chambre 1", "Chambre 2"}


async def test_create_place_full_bad_owner_returns_422(authedClient: AsyncClient):
    resp = await authedClient.post(
        "/api/v1/places/full",
        json={
            "place": {"name": "X", "ownerId": 99999},
            "units": [],
        },
    )
    assert resp.status_code == 422


async def test_create_tenant_full_creates_rents_and_caution(authedClient: AsyncClient):
    data = await _createPlaceWithUnits(authedClient)
    unit_id = data["units"][0]["id"]

    resp = await authedClient.post(
        "/api/v1/tenants/full",
        json={
            "tenant": {
                "firstName": "Alice",
                "name": "Martin",
                "email": "alice@test.com",
                "placeUnitId": unit_id,
                "withdrawDay": 5,
                "dateEntrance": "2026-04-01T00:00:00",
            },
            "rents": {
                "loyer": {"price": 800},
                "charges": {"price": 100},
                "garantie": {"price": 1600},
            },
            "cautionReceipt": {
                "amount": 1600,
                "periodBegin": "2026-04-01T00:00:00",
                "paid": 1,
            },
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["tenant"]["firstName"] == "Alice"
    assert body["tenant"]["placeUnitId"] == unit_id
    assert body["tenant"]["warantyReceiptId"] is not None

    rents = body["rents"]
    assert len(rents) == 3
    types = sorted(r["type"] for r in rents)
    assert types == ["Charges", "Garantie", "Loyer"]
    prices_by_type = {r["type"]: r["price"] for r in rents}
    assert prices_by_type["Loyer"] == 800
    assert prices_by_type["Charges"] == 100
    assert prices_by_type["Garantie"] == 1600

    assert body["cautionReceipt"] is not None
    assert body["cautionReceipt"]["amount"] == 1600
    assert body["tenant"]["warantyReceiptId"] == body["cautionReceipt"]["id"]


async def test_create_tenant_full_without_caution(authedClient: AsyncClient):
    data = await _createPlaceWithUnits(authedClient)
    unit_id = data["units"][0]["id"]

    resp = await authedClient.post(
        "/api/v1/tenants/full",
        json={
            "tenant": {
                "firstName": "Bob",
                "name": "Durand",
                "placeUnitId": unit_id,
                "withdrawDay": 1,
            },
            "rents": {
                "loyer": {"price": 500},
                "charges": {"price": 50},
                "garantie": {"price": 1000},
            },
            "cautionReceipt": None,
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["cautionReceipt"] is None
    assert body["tenant"]["warantyReceiptId"] is None


async def test_get_tenant_receipts(authedClient: AsyncClient):
    data = await _createPlaceWithUnits(authedClient)
    unit_id = data["units"][0]["id"]

    tenant_resp = await authedClient.post(
        "/api/v1/tenants/full",
        json={
            "tenant": {"firstName": "Rita", "placeUnitId": unit_id, "withdrawDay": 1},
            "rents": {
                "loyer": {"price": 600},
                "charges": {"price": 60},
                "garantie": {"price": 1200},
            },
            "cautionReceipt": {"amount": 1200, "periodBegin": "2026-01-15T00:00:00", "paid": 1},
        },
    )
    tenant_id = tenant_resp.json()["tenant"]["id"]

    # Add extra receipts
    await authedClient.post("/api/v1/rentReceipts", json={
        "tenantId": tenant_id, "amount": 600, "periodBegin": "2026-02-01T00:00:00", "paid": 1
    })
    await authedClient.post("/api/v1/rentReceipts", json={
        "tenantId": tenant_id, "amount": 600, "periodBegin": "2026-03-01T00:00:00", "paid": 0
    })

    resp = await authedClient.get(f"/api/v1/tenants/{tenant_id}/receipts")
    assert resp.status_code == 200
    receipts = resp.json()
    assert len(receipts) == 3
    # Sorted by periodBegin DESC (March > February > January)
    months = [r["periodBegin"][:7] for r in receipts]
    assert months == ["2026-03", "2026-02", "2026-01"]


async def test_dashboard_occupancy(authedClient: AsyncClient):
    data = await _createPlaceWithUnits(authedClient)
    unit_regular = data["units"][0]
    unit_coloc = data["units"][1]
    room1 = unit_coloc["rooms"][0]

    # Tenant in regular unit — paid this month
    await authedClient.post(
        "/api/v1/tenants/full",
        json={
            "tenant": {"firstName": "Alice", "placeUnitId": unit_regular["id"], "withdrawDay": 1},
            "rents": {"loyer": {"price": 800}, "charges": {"price": 100}, "garantie": {"price": 1600}},
            "cautionReceipt": None,
        },
    )
    # Get her id
    tenants_list = (await authedClient.get("/api/v1/tenants")).json()
    alice = next(t for t in tenants_list if t["firstName"] == "Alice")
    await authedClient.post("/api/v1/rentReceipts", json={
        "tenantId": alice["id"], "amount": 800, "periodBegin": "2026-04-10T00:00:00", "paid": 1
    })

    # Tenant in flatshare room — NOT paid this month
    await authedClient.post(
        "/api/v1/tenants/full",
        json={
            "tenant": {
                "firstName": "Bob",
                "placeUnitId": unit_coloc["id"],
                "placeUnitRoomId": room1["id"],
                "withdrawDay": 1,
            },
            "rents": {"loyer": {"price": 400}, "charges": {"price": 50}, "garantie": {"price": 800}},
            "cautionReceipt": None,
        },
    )

    resp = await authedClient.get("/api/v1/dashboard/occupancy?month=2026-04")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["month"] == "2026-04"
    assert len(body["places"]) == 1
    place = body["places"][0]
    assert place["placeName"] == "Immeuble Test"
    assert place["ownerName"] == "The Owner"
    assert len(place["units"]) == 2

    regular = next(u for u in place["units"] if u["unitId"] == unit_regular["id"])
    coloc = next(u for u in place["units"] if u["unitId"] == unit_coloc["id"])

    # Regular unit: Alice paid
    assert regular["flatshare"] is False
    assert len(regular["tenants"]) == 1
    assert regular["tenants"][0]["firstName"] == "Alice"
    assert regular["tenants"][0]["rentPaid"] is True
    assert regular["tenants"][0]["rentAmount"] == 800

    # Coloc unit: Bob in room 1, not paid
    assert coloc["flatshare"] is True
    assert coloc["tenants"] == []
    assert len(coloc["rooms"]) == 2
    room_one = next(r for r in coloc["rooms"] if r["roomId"] == room1["id"])
    assert len(room_one["tenants"]) == 1
    assert room_one["tenants"][0]["firstName"] == "Bob"
    assert room_one["tenants"][0]["rentPaid"] is False
    assert room_one["tenants"][0]["rentAmount"] == 400


async def test_dashboard_occupancy_invalid_month(authedClient: AsyncClient):
    resp = await authedClient.get("/api/v1/dashboard/occupancy?month=not-a-date")
    assert resp.status_code == 422


async def test_users_admin_only_create(authedClient: AsyncClient, client: AsyncClient):
    # Admin (authedClient) creates a non-admin user
    resp = await authedClient.post(
        "/api/v1/users",
        json={"email": "user@test.com", "password": "pass1234", "isAdmin": 0},
    )
    assert resp.status_code == 201

    # Non-admin logs in
    nonAdminClient = client
    # (we reuse `client` as a fresh un-auth'd client; need to clear its cookies first)
    nonAdminClient.cookies.clear()
    login = await nonAdminClient.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "pass1234"},
    )
    assert login.status_code == 200

    # Non-admin tries to create another user → 403
    resp = await nonAdminClient.post(
        "/api/v1/users",
        json={"email": "x@test.com", "password": "pass", "isAdmin": 0},
    )
    assert resp.status_code == 403

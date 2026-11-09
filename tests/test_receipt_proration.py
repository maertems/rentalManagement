"""Tests de proratisation des quittances (entrée / sortie en cours de mois)."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_tenant(
    authedClient: AsyncClient,
    email: str,
    *,
    dateEntrance: str | None = None,
    dateExit: str | None = None,
) -> int:
    user = await authedClient.post(
        "/api/v1/users", json={"email": email, "password": "password123"}
    )
    owner = await authedClient.post(
        "/api/v1/owners", json={"name": "Owner", "userId": user.json()["id"]}
    )
    place = await authedClient.post(
        "/api/v1/places",
        json={"name": "Place", "ownerId": owner.json()["id"]},
    )
    unit = await authedClient.post(
        "/api/v1/placesUnits",
        json={"name": "Unit", "placeId": place.json()["id"]},
    )

    tenant_data = {
        "firstName": "Test",
        "name": "Tenant",
        "placeUnitId": unit.json()["id"],
        "withdrawDay": 1,
    }
    if dateEntrance:
        tenant_data["dateEntrance"] = dateEntrance
    if dateExit:
        tenant_data["dateExit"] = dateExit

    resp = await authedClient.post(
        "/api/v1/tenants/full",
        json={
            "tenant": tenant_data,
            "rents": {
                "loyer": {"price": 800},
                "charges": {"price": 100},
                "garantie": {"price": 1600},
            },
            "cautionReceipt": None,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["tenant"]["id"]


async def _generate(authedClient: AsyncClient, tenant_id: int, month: str):
    return await authedClient.post(
        "/api/v1/rentReceipts/generate",
        json={"tenantId": tenant_id, "month": month},
    )


async def _details(authedClient: AsyncClient, receipt_id: int) -> dict[str, float]:
    resp = await authedClient.get(
        "/api/v1/rentReceiptsDetails", params={"rentReceiptsId": receipt_id}
    )
    assert resp.status_code == 200, resp.text
    return {d["description"]: float(d["price"]) for d in resp.json()}


async def test_exit_mid_month_prorates_rent_and_charges(authedClient: AsyncClient):
    """Sortie le 09/04 → 9 jours sur 30 ; les frais ponctuels restent entiers."""
    tenant_id = await _create_tenant(
        authedClient, "prorata_exit@test.com", dateExit="2026-04-09T00:00:00"
    )
    fee = await authedClient.post(
        "/api/v1/rentsFees",
        json={
            "tenantId": tenant_id,
            "applicationMonth": "2026-04-01T00:00:00",
            "description": "Travaux",
            "price": 150,
        },
    )
    assert fee.status_code == 201, fee.text

    resp = await _generate(authedClient, tenant_id, "2026-04")
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["periodBegin"] == "2026-04-01T00:00:00"
    assert body["periodEnd"] == "2026-04-09T00:00:00"
    assert float(body["amount"]) == 420.00  # 240 + 30 + 150

    details = await _details(authedClient, body["id"])
    assert details == {"Loyer": 240.00, "Charges": 30.00, "Travaux": 150.00}


async def test_entrance_mid_month_prorates_from_entrance_date(
    authedClient: AsyncClient,
):
    """Entrée le 15/04 → 16 jours sur 30 (15 inclus)."""
    tenant_id = await _create_tenant(
        authedClient, "prorata_entrance@test.com", dateEntrance="2026-04-15T00:00:00"
    )

    resp = await _generate(authedClient, tenant_id, "2026-04")
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["periodBegin"] == "2026-04-15T00:00:00"
    assert body["periodEnd"] == "2026-04-30T00:00:00"
    assert float(body["amount"]) == 479.00  # 426 + 53 (euro inférieur)

    details = await _details(authedClient, body["id"])
    assert details == {"Loyer": 426.00, "Charges": 53.00}


async def test_exit_after_month_keeps_full_amount(authedClient: AsyncClient):
    """Sortie en mai : le mois d'avril reste facturé en entier."""
    tenant_id = await _create_tenant(
        authedClient, "prorata_after@test.com", dateExit="2026-05-05T00:00:00"
    )

    resp = await _generate(authedClient, tenant_id, "2026-04")
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["periodBegin"] == "2026-04-01T00:00:00"
    assert body["periodEnd"] == "2026-04-30T00:00:00"
    assert float(body["amount"]) == 900.00


async def test_exit_before_month_returns_400(authedClient: AsyncClient):
    """Locataire déjà sorti avant le mois demandé : aucune quittance possible."""
    tenant_id = await _create_tenant(
        authedClient, "prorata_before@test.com", dateExit="2026-03-09T00:00:00"
    )

    resp = await _generate(authedClient, tenant_id, "2026-04")
    assert resp.status_code == 400, resp.text
    assert "n'occupe pas" in resp.json()["detail"]

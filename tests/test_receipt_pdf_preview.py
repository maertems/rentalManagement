"""Tests de consultation des PDF : génération à la volée sans stockage serveur."""
import pytest
from httpx import AsyncClient

from tests.test_receipt_proration import _create_tenant, _generate

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_preview_avis_is_generated_on_the_fly_without_being_stored(
    authedClient: AsyncClient,
):
    tenant_id = await _create_tenant(authedClient, "preview_avis@test.com")
    generated = await _generate(authedClient, tenant_id, "2026-04")
    receipt_id = generated.json()["id"]

    before = await authedClient.get(f"/api/v1/rentReceipts/{receipt_id}")
    assert before.json()["pdfFilename"] is None

    resp = await authedClient.get(
        f"/api/v1/rentReceipts/{receipt_id}/pdf",
        params={"doc_type": "avis"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content.startswith(b"%PDF")

    after = await authedClient.get(f"/api/v1/rentReceipts/{receipt_id}")
    assert after.json()["pdfFilename"] is None


async def test_preview_quittance_requires_paid_receipt(
    authedClient: AsyncClient,
):
    tenant_id = await _create_tenant(authedClient, "preview_quittance@test.com")
    generated = await _generate(authedClient, tenant_id, "2026-04")
    receipt_id = generated.json()["id"]

    unpaid = await authedClient.get(
        f"/api/v1/rentReceipts/{receipt_id}/pdf",
        params={"doc_type": "quittance"},
    )
    assert unpaid.status_code == 409, unpaid.text

    await authedClient.patch(
        f"/api/v1/rentReceipts/{receipt_id}", json={"paid": 1}
    )

    paid = await authedClient.get(
        f"/api/v1/rentReceipts/{receipt_id}/pdf",
        params={"doc_type": "quittance"},
    )
    assert paid.status_code == 200, paid.text
    assert paid.content.startswith(b"%PDF")

    # L'avis reste consultable après paiement, sans être stocké.
    avis = await authedClient.get(
        f"/api/v1/rentReceipts/{receipt_id}/pdf",
        params={"doc_type": "avis"},
    )
    assert avis.status_code == 200, avis.text
    assert avis.content.startswith(b"%PDF")


async def test_preview_garantie_rejects_regular_receipt(
    authedClient: AsyncClient,
):
    tenant_id = await _create_tenant(authedClient, "preview_garantie@test.com")
    generated = await _generate(authedClient, tenant_id, "2026-04")
    receipt_id = generated.json()["id"]

    resp = await authedClient.get(
        f"/api/v1/rentReceipts/{receipt_id}/pdf",
        params={"doc_type": "garantie"},
    )
    assert resp.status_code == 400, resp.text

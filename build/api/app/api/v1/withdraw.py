"""
Withdraw validation — endpoint appelé par le cron externe lors d'une notification bancaire.

Algorithme identique à l'ancienne version PHP (withdrawValidation.php) :
1. Nettoyer le montant (remplacer ',' → '.', supprimer espaces et '+')
2. Chercher le locataire par withdrawName (insensible à la casse)
3. Trouver la première quittance impayée dont le montant correspond, triée par periodBegin ASC
4. Vérifier si c'est une garantie (description == "Garantie", correspondance exacte)
5. Générer le PDF (QuittanceGarantie ou QuittanceLoyer)
6. Si garantie : mettre à jour tenant.warantyReceiptId
7. Marquer la quittance comme payée (paid = True)
8. Envoyer l'email si tenant.sendLeaseRental == 1
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_withdraw_user
from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.rentReceipt import RentReceipt
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.models.placesUnit import PlacesUnit
from app.models.place import Place
from app.models.owner import Owner
from app.services.email import send_pdf_email_sync
from app.services.pdf_context import get_receipt_context
from app.services.pdf_generator import generate_receipt_pdf

FILES_DIR = Path("/app/files")

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

router = APIRouter(
    prefix="/withdraw",
    tags=["Withdraw"],
    dependencies=[Depends(get_withdraw_user)],
)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class WithdrawInput(BaseModel):
    name: str   # withdrawName du locataire (insensible à la casse)
    rent: str   # montant brut depuis la banque (ex: "800,00" ou "800.00" ou "+800 00")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/validate",
    summary="Valider un paiement bancaire : génère la quittance et marque la quittance comme payée",
)
async def validate_withdrawal(
    payload: WithdrawInput,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:

    log: dict[str, Any] = {"inputName": payload.name, "inputRent": payload.rent}

    # --- 1. Nettoyer le montant (identique au PHP : remplace ',' '.', retire espaces et '+')
    rent_str = payload.rent.replace(",", ".").replace(" ", "").replace("+", "")
    try:
        rent_amount = float(rent_str)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid rent amount")

    # --- 2. Chercher le locataire par withdrawName (insensible à la casse)
    result = await db.execute(
        select(Tenant).where(
            func.upper(Tenant.withdrawName) == payload.name.upper()
        )
    )
    tenant = result.scalars().first()

    if not tenant:
        return {"status": "500", "message": "tenant not found", "log": log}

    log["tenantId"] = tenant.id

    # --- 3. Trouver la première quittance impayée avec le bon montant (periodBegin ASC)
    result = await db.execute(
        select(RentReceipt)
        .where(
            RentReceipt.tenantId == tenant.id,
            RentReceipt.paid == False,  # noqa: E712
            RentReceipt.amount == rent_amount,
        )
        .order_by(RentReceipt.periodBegin.asc())
        .limit(1)
    )
    receipt = result.scalars().first()

    if not receipt:
        log["message"] = "no receipt to validate found"
        return {"status": "210", "message": "no receipt to validate found", "log": log}

    log["receiptId"] = receipt.id
    log["amount"] = {"fromInput": rent_amount, "fromDB": float(receipt.amount)}

    # --- 4. Récupérer les détails (triés par sortOrder)
    details_rows = (
        await db.execute(
            select(RentReceiptsDetail)
            .where(RentReceiptsDetail.rentReceiptsId == receipt.id)
            .order_by(RentReceiptsDetail.sortOrder)
        )
    ).scalars().all()

    for d in details_rows:
        log.setdefault("receiptDesc", "")
        log["receiptDesc"] += f"{d.description} : {d.price}\n"

    # --- 4b. isGarantie : correspondance exacte "Garantie" (identique au PHP)
    is_garantie = any(d.description == "Garantie" for d in details_rows)
    log["isGarantie"] = is_garantie

    # --- 5. Charger unit / place / owner pour l'email
    unit = await db.get(PlacesUnit, tenant.placeUnitId) if tenant.placeUnitId else None
    place = await db.get(Place, unit.placeId) if unit else None
    owner = await db.get(Owner, place.ownerId) if place else None

    unit_friendly = (unit.friendlyName or unit.name or "") if unit else ""
    owner_email = (owner.email or "") if owner else ""
    owner_name = (owner.name or "") if owner else ""
    tenant_email = tenant.email or ""
    tenant_name = " ".join(filter(None, [tenant.firstName, tenant.name]))

    # --- 6. Générer le PDF (avant de marquer payé, identique au PHP)
    # receipt.paid est encore False → on force le type pour éviter la génération d'un avis
    doc_type_override = "garantie" if is_garantie else "quittance"
    ctx = await get_receipt_context(db, receipt.id, doc_type_override=doc_type_override)

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = FILES_DIR / ctx.filename

    if file_path.exists():
        pdf_bytes = file_path.read_bytes()
    else:
        pdf_bytes = generate_receipt_pdf(ctx, doc_type_override=doc_type_override)
        file_path.write_bytes(pdf_bytes)

    log["filename"] = ctx.filename

    # --- 7. Si garantie : lier la quittance au locataire (identique au PHP updateTenant)
    if is_garantie:
        tenant.warantyReceiptId = receipt.id

    # --- 8. Marquer la quittance comme payée + persister le nom du PDF
    receipt.paid = True
    receipt.pdfFilename = ctx.filename
    await db.commit()
    log["updatePaid"] = 1

    # --- 9. Envoyer l'email selon sendLeaseRental (flag DB, pas forcé)
    send_email_flag = (
        bool(tenant.sendLeaseRental)
        and bool(tenant_email)
        and bool(owner_email)
    )
    log["emailSent"] = send_email_flag

    if send_email_flag:
        period_begin = receipt.periodBegin
        month_name = MONTHS_FR[period_begin.month - 1] if period_begin else ""
        year = period_begin.year if period_begin else ""

        if is_garantie:
            subject = "Reçu de garantie"
            if unit_friendly:
                subject += f" - {unit_friendly}"
            body = (
                f"Bonjour,\n\n"
                f"Vous trouverez ci-joint le reçu du dépot de garantie.\n"
                f"Vous souhaitant bonne réception.\n\n"
                f"Bonne journée,\n"
                f"{owner_name}\n"
            )
        else:
            subject = "Quittance de loyer"
            if unit_friendly:
                subject += f" - {unit_friendly}"
            body = (
                f"Bonjour,\n\n"
                f"Vous trouverez ci-joint la quittance pour le loyer du mois de {month_name} {year}.\n"
                f"Vous souhaitant bonne réception.\n\n"
                f"Bonne journée,\n"
                f"{owner_name}\n"
            )

        background_tasks.add_task(
            send_pdf_email_sync,
            from_addr=owner_email,
            from_name=owner_name,
            to_addr=tenant_email,
            to_name=tenant_name,
            subject=subject,
            body=body,
            pdf_bytes=pdf_bytes,
            pdf_filename=ctx.filename,
            property_name=f"{ctx.unit_zip}-{ctx.place_name}",
        )

    return {"status": 100, "log": log}

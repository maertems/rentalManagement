"""
Cron journalier — Génération automatique des avis d'échéance.

Lancé tous les jours à 07h00 (heure locale du container, UTC par défaut en Docker).
Pour chaque propriétaire :
  1. Lire rentReceiptDay dans params.yaml (défaut 25), clamper au dernier jour du mois.
  2. Si aujourd'hui == ce jour → générer les quittances pour tous les locataires actifs
     qui n'ont pas encore de quittance pour ce mois-ci.
  3. Envoyer l'avis d'échéance par email si sendNoticeOfLeaseRental == 1.

Idempotent : si une quittance existe déjà pour ce mois et ce locataire, on passe.
"""
from __future__ import annotations

import calendar
import logging
import re
import unicodedata
from datetime import datetime, date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.owner import Owner
from app.models.place import Place
from app.models.placesUnit import PlacesUnit
from app.models.tenant import Tenant
from app.models.rent import Rent
from app.models.rentReceipt import RentReceipt
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.models.rentsFee import RentsFee
from app.services.email import send_pdf_email_async
from app.services.params import get_owner_params
from app.services.pdf_context import get_receipt_context
from app.services.pdf_generator import generate_receipt_pdf

logger = logging.getLogger("uvicorn")
FILES_DIR = Path("/app/files")
FEES_DIR = Path("/app/files/fees")

# Ordre d'affichage des lignes dans le détail (Loyer d'abord, Charges ensuite)
_RENT_TYPE_ORDER: dict[str, int] = {"Loyer": 0, "Charges": 1}

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


# ---------------------------------------------------------------------------
# Helpers dates
# ---------------------------------------------------------------------------

def _clamp_day(day: int, year: int, month: int) -> int:
    """Clampe le jour au dernier jour du mois (ex: 31 en février → 28/29)."""
    _, last = calendar.monthrange(year, month)
    return min(day, last)


def _period_begin(year: int, month: int) -> datetime:
    return datetime(year, month, 1, 0, 0, 0)


def _period_end(year: int, month: int) -> datetime:
    _, last = calendar.monthrange(year, month)
    return datetime(year, month, last, 0, 0, 0)


def _next_period_begin(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year + 1, 1, 1)
    return datetime(year, month + 1, 1)


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------

async def _receipt_exists(
    db: AsyncSession, tenant_id: int, year: int, month: int
) -> bool:
    """Retourne True si une quittance existe déjà pour ce locataire et ce mois."""
    result = await db.execute(
        select(RentReceipt)
        .where(
            RentReceipt.tenantId == tenant_id,
            RentReceipt.periodBegin >= _period_begin(year, month),
            RentReceipt.periodBegin < _next_period_begin(year, month),
        )
        .limit(1)
    )
    return result.scalars().first() is not None


# ---------------------------------------------------------------------------
# Génération pour un locataire
# ---------------------------------------------------------------------------

async def _create_receipt_for_tenant(
    db: AsyncSession, tenant: Tenant, year: int, month: int
) -> None:
    """Crée un RentReceipt + détails + PDF AvisEcheance pour un locataire."""
    label = f"Tenant {tenant.id} ({((tenant.firstName or '') + ' ' + (tenant.name or '')).strip()})"

    # Loyers actifs, hors Garantie
    rents = (
        await db.execute(
            select(Rent).where(
                Rent.tenantId == tenant.id,
                Rent.active == 1,
                Rent.type != "Garantie",
            )
        )
    ).scalars().all()

    if not rents:
        logger.info("    %s: aucun loyer actif, ignoré", label)
        return

    # Frais du mois (rentsFees dont applicationMonth est dans le mois year/month)
    period_begin = _period_begin(year, month)
    period_end = _period_end(year, month)
    fees = (
        await db.execute(
            select(RentsFee).where(
                RentsFee.tenantId == tenant.id,
                RentsFee.applicationMonth >= period_begin,
                RentsFee.applicationMonth <= period_end,
            )
        )
    ).scalars().all()

    amount = sum(float(r.price or 0) for r in rents) + sum(float(f.price or 0) for f in fees)

    # Créer la quittance
    receipt = RentReceipt(
        tenantId=tenant.id,
        placeUnitId=tenant.placeUnitId,
        placeUnitRoomId=tenant.placeUnitRoomId,
        amount=amount,
        periodBegin=period_begin,
        periodEnd=period_end,
        paid=0,
    )
    db.add(receipt)
    await db.flush()  # obtenir receipt.id

    # Lignes de détail : Loyer → Charges → autres rents → rentsFees du mois
    sorted_rents = sorted(rents, key=lambda r: _RENT_TYPE_ORDER.get(r.type or "", 99))
    detail_order = 1
    for rent in sorted_rents:
        db.add(
            RentReceiptsDetail(
                rentReceiptsId=receipt.id,
                sortOrder=detail_order,
                description=rent.type,
                price=rent.price,
            )
        )
        detail_order += 1
    for fee in fees:
        db.add(
            RentReceiptsDetail(
                rentReceiptsId=receipt.id,
                sortOrder=detail_order,
                description=fee.description,
                price=fee.price,
            )
        )
        detail_order += 1
    await db.flush()

    # Générer le PDF — AvisEcheance (non payé)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    ctx = None
    pdf_bytes: bytes | None = None
    try:
        ctx = await get_receipt_context(db, receipt.id, doc_type_override="avis")
        file_path = FILES_DIR / ctx.filename
        if file_path.exists():
            pdf_bytes = file_path.read_bytes()
        else:
            pdf_bytes = generate_receipt_pdf(ctx, doc_type_override="avis")
            file_path.write_bytes(pdf_bytes)
        receipt.pdfFilename = ctx.filename
        logger.info("    %s: PDF → %s", label, ctx.filename)
    except Exception as exc:
        logger.warning("    %s: échec génération PDF : %s", label, exc)

    await db.commit()
    logger.info(
        "    %s: quittance créée (id=%d, montant=%.2f €)",
        label, receipt.id, amount,
    )

    # Envoyer l'avis d'échéance si :
    # - case cochée (sendNoticeOfLeaseRental) OU présence de rentsFees dans la quittance
    should_send_email = bool(tenant.sendNoticeOfLeaseRental) or len(fees) > 0
    if (
        ctx is not None
        and pdf_bytes is not None
        and should_send_email
        and tenant.email
        and ctx.owner_email
    ):
        # Collecter les justificatifs des rentsFees
        month_prefix = _period_begin(year, month).strftime("%Y-%m")
        extra_attachments: list[tuple[bytes, str]] = []
        for fee in fees:
            if FEES_DIR.exists():
                doc = next(FEES_DIR.glob(f"{fee.id}.*"), None)
                if doc:
                    raw = (fee.description or "document").strip()
                    raw = unicodedata.normalize("NFD", raw).encode("ascii", "ignore").decode("ascii")
                    desc = re.sub(r"[^a-zA-Z0-9._-]", "-", raw)
                    desc = re.sub(r"-+", "-", desc).strip("-") or "document"
                    email_name = f"{month_prefix}.{desc}{doc.suffix}"
                    extra_attachments.append((doc.read_bytes(), email_name))

        period = receipt.periodBegin
        month_name = MONTHS_FR[period.month - 1] if period else ""
        yr = period.year if period else year
        unit_friendly = ctx.unit_name or ctx.place_name
        subject = f"Avis d'échéance - {unit_friendly}" if unit_friendly else "Avis d'échéance"
        body = (
            f"Bonjour,\n\n"
            f"Vous trouverez ci-joint l'avis d'échéance du mois de {month_name} {yr}.\n"
            f"Vous souhaitant bonne réception.\n\n"
            f"Bonne journée,\n"
            f"{ctx.owner_name}\n"
        )
        try:
            await send_pdf_email_async(
                from_addr=ctx.owner_email,
                from_name=ctx.owner_name,
                to_addr=tenant.email,
                to_name=ctx.tenant_fullname,
                subject=subject,
                body=body,
                pdf_bytes=pdf_bytes,
                pdf_filename=ctx.filename,
                extra_attachments=extra_attachments,
            )
            logger.info("    %s: email avis d'échéance envoyé à %s", label, tenant.email)
        except Exception as exc:
            logger.warning("    %s: échec envoi email : %s", label, exc)


# ---------------------------------------------------------------------------
# Point d'entrée du cron
# ---------------------------------------------------------------------------

async def run_daily_receipt_generation() -> None:
    """
    Tâche cron quotidienne — lancée à 07h00.

    Pour chaque propriétaire, vérifie si aujourd'hui correspond à son jour de
    génération (rentReceiptDay dans params.yaml, défaut 25, clampé au dernier
    jour du mois). Si oui, crée les avis d'échéance pour tous les locataires
    actifs sans quittance pour ce mois.
    """
    today = date.today()
    logger.info("[cron] daily_receipt_generation — %s", today.isoformat())

    async with AsyncSessionLocal() as db:
        owners = (await db.execute(select(Owner))).scalars().all()
        logger.info("[cron] %d propriétaire(s) trouvé(s)", len(owners))

        for owner in owners:
            params = get_owner_params(owner.id)
            configured_day = int(params.get("rentReceiptDay") or 25)
            clamped_day = _clamp_day(configured_day, today.year, today.month)

            if today.day != clamped_day:
                # Pas le bon jour pour ce propriétaire
                continue

            logger.info(
                "[cron] Owner %d (%s) : jour de génération %d → traitement",
                owner.id, owner.name, clamped_day,
            )

            # Tous les biens → logements → locataires actifs
            places = (
                await db.execute(select(Place).where(Place.ownerId == owner.id))
            ).scalars().all()

            for place in places:
                units = (
                    await db.execute(
                        select(PlacesUnit).where(PlacesUnit.placeId == place.id)
                    )
                ).scalars().all()

                for unit in units:
                    tenants = (
                        await db.execute(
                            select(Tenant).where(
                                Tenant.placeUnitId == unit.id,
                                Tenant.active == 1,
                            )
                        )
                    ).scalars().all()

                    for tenant in tenants:
                        if await _receipt_exists(db, tenant.id, today.year, today.month):
                            logger.info(
                                "    Tenant %d : quittance déjà présente pour %d-%02d, ignoré",
                                tenant.id, today.year, today.month,
                            )
                            continue
                        await _create_receipt_for_tenant(db, tenant, today.year, today.month)

    logger.info("[cron] daily_receipt_generation — terminé")

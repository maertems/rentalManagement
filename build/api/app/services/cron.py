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
from datetime import datetime, date, time
from decimal import Decimal, ROUND_FLOOR
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


def _occupied_window(
    tenant: Tenant, year: int, month: int
) -> tuple[date, date] | None:
    """
    Fenêtre d'occupation du locataire pour le mois demandé, bornée par
    dateEntrance et dateExit (jours inclusifs). Retourne None si le locataire
    n'occupe pas le logement sur ce mois.
    """
    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    entrance = tenant.dateEntrance.date() if tenant.dateEntrance else None
    exit_ = tenant.dateExit.date() if tenant.dateExit else None

    # Locataire pas encore entré ou déjà sorti avant/après le mois
    if entrance and entrance > month_end:
        return None
    if exit_ and exit_ < month_start:
        return None
    if entrance and exit_ and entrance > exit_:
        return None

    start = max(month_start, entrance) if entrance else month_start
    end = min(month_end, exit_) if exit_ else month_end
    return start, end


def _round_euro(price: float | Decimal | None) -> Decimal:
    """Arrondit un montant à l'euro inférieur (aucun centime sur les lignes)."""
    return Decimal(str(price or 0)).quantize(Decimal("1"), rounding=ROUND_FLOOR)


def _prorate_price(price: float | Decimal | None, days: int, days_in_month: int) -> Decimal:
    """Proratise un montant mensuel au nombre de jours occupés, arrondi à l'euro inférieur."""
    monthly = Decimal(str(price or 0))
    return _round_euro(monthly * days / days_in_month)


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------

async def _receipt_exists(
    db: AsyncSession,
    tenant_id: int,
    year: int,
    month: int,
    exclude_receipt_id: int | None = None,
) -> bool:
    """
    Retourne True si une quittance de loyer existe déjà pour ce locataire et ce
    mois. Le reçu de dépôt de garantie (warantyReceiptId) est ignoré : ce n'est
    pas une quittance de loyer et il ne doit pas bloquer la facturation du mois.
    """
    stmt = select(RentReceipt).where(
        RentReceipt.tenantId == tenant_id,
        RentReceipt.periodBegin >= _period_begin(year, month),
        RentReceipt.periodBegin < _next_period_begin(year, month),
    )
    if exclude_receipt_id is not None:
        stmt = stmt.where(RentReceipt.id != exclude_receipt_id)
    result = await db.execute(stmt.limit(1))
    return result.scalars().first() is not None


# ---------------------------------------------------------------------------
# Génération pour un locataire
# ---------------------------------------------------------------------------

class NoActiveRentError(Exception):
    """Le locataire n'a aucun loyer actif (hors Garantie) : rien à facturer."""


class ReceiptAlreadyExistsError(Exception):
    """Une quittance existe déjà pour ce locataire et ce mois."""


class TenantNotInPeriodError(Exception):
    """Le locataire n'occupe pas le logement sur le mois demandé (entrée/sortie)."""


async def create_receipt_entry(
    db: AsyncSession, tenant: Tenant, year: int, month: int
) -> tuple[RentReceipt, list[RentsFee]]:
    """
    Crée l'entrée RentReceipt + ses lignes RentReceiptsDetail pour un mois donné.

    Montant = somme des loyers actifs (hors Garantie) + frais ponctuels du mois.
    Si le locataire entre ou sort en cours de mois (dateEntrance / dateExit),
    les loyers et charges sont proratisés au nombre de jours occupés et arrondis
    à l'euro inférieur ; les frais ponctuels restent facturés en totalité, tels
    quels. La période de la quittance est alors bornée aux dates d'occupation.
    Ne génère ni PDF ni email, ne commit pas (flush uniquement).

    Lève NoActiveRentError si aucun loyer actif, ReceiptAlreadyExistsError si
    une quittance existe déjà pour ce mois, TenantNotInPeriodError si le
    locataire n'occupe pas le logement sur ce mois.
    """
    if await _receipt_exists(
        db, tenant.id, year, month, exclude_receipt_id=tenant.warantyReceiptId
    ):
        raise ReceiptAlreadyExistsError()

    window = _occupied_window(tenant, year, month)
    if window is None:
        raise TenantNotInPeriodError()
    occupied_begin, occupied_end = window
    days_in_month = calendar.monthrange(year, month)[1]
    days_occupied = (occupied_end - occupied_begin).days + 1
    is_prorated = days_occupied < days_in_month

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
        raise NoActiveRentError()

    # Frais du mois (rentsFees dont applicationMonth est dans le mois year/month)
    period_begin = _period_begin(year, month)
    period_end = _period_end(year, month)
    fees = list(
        (
            await db.execute(
                select(RentsFee).where(
                    RentsFee.tenantId == tenant.id,
                    RentsFee.applicationMonth >= period_begin,
                    RentsFee.applicationMonth <= period_end,
                )
            )
        ).scalars().all()
    )

    # Montant de chaque ligne récurrente (loyer / charges) — proratisé si besoin,
    # toujours arrondi à l'euro inférieur (pas de centimes sur les lignes).
    rent_prices: dict[int, Decimal] = {
        rent.id: (
            _prorate_price(rent.price, days_occupied, days_in_month)
            if is_prorated
            else _round_euro(rent.price)
        )
        for rent in rents
    }

    amount = sum(rent_prices.values(), Decimal("0.00")) + sum(
        (Decimal(str(f.price or 0)) for f in fees), Decimal("0.00")
    )

    receipt = RentReceipt(
        tenantId=tenant.id,
        placeUnitId=tenant.placeUnitId,
        placeUnitRoomId=tenant.placeUnitRoomId,
        amount=amount,
        periodBegin=datetime.combine(occupied_begin, time.min),
        periodEnd=datetime.combine(occupied_end, time.min),
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
                price=rent_prices[rent.id],
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

    return receipt, fees


async def _create_receipt_for_tenant(
    db: AsyncSession, tenant: Tenant, year: int, month: int
) -> None:
    """Crée un RentReceipt + détails + PDF AvisEcheance pour un locataire."""
    label = f"Tenant {tenant.id} ({((tenant.firstName or '') + ' ' + (tenant.name or '')).strip()})"

    try:
        receipt, fees = await create_receipt_entry(db, tenant, year, month)
    except NoActiveRentError:
        logger.info("    %s: aucun loyer actif, ignoré", label)
        return
    except ReceiptAlreadyExistsError:
        logger.info("    %s: quittance déjà présente pour %d-%02d, ignoré", label, year, month)
        return
    except TenantNotInPeriodError:
        logger.info(
            "    %s: hors période d'occupation pour %d-%02d, ignoré", label, year, month
        )
        return
    amount = float(receipt.amount or 0)

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
                property_name=f"{ctx.unit_zip}-{ctx.place_name}",
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

            # L'avis d'échéance généré le 25 avril concerne le loyer de MAI → mois suivant
            next_period = _next_period_begin(today.year, today.month)
            target_year, target_month = next_period.year, next_period.month

            logger.info(
                "[cron] Owner %d (%s) : jour de génération %d → traitement pour %d-%02d",
                owner.id, owner.name, clamped_day, target_year, target_month,
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
                        if await _receipt_exists(
                            db,
                            tenant.id,
                            target_year,
                            target_month,
                            exclude_receipt_id=tenant.warantyReceiptId,
                        ):
                            logger.info(
                                "    Tenant %d : quittance déjà présente pour %d-%02d, ignoré",
                                tenant.id, target_year, target_month,
                            )
                            continue
                        await _create_receipt_for_tenant(db, tenant, target_year, target_month)

    logger.info("[cron] daily_receipt_generation — terminé")

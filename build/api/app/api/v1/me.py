import asyncio
import calendar
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.owner import Owner
from app.models.place import Place
from app.models.placesUnit import PlacesUnit
from app.models.tenant import Tenant
from app.models.rent import Rent
from app.models.rentReceipt import RentReceipt
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.models.rentsFee import RentsFee
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.schemas.user import UserRead
from app.schemas.owner import OwnerRead
from app.services.email import send_pdf_email_sync
from app.services.pdf_context import get_receipt_context
from app.services.pdf_generator import generate_receipt_pdf

FILES_DIR = Path("/app/files")
FEES_DIR = Path("/app/files/fees")

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

_RENT_TYPE_ORDER: dict[str, int] = {"Loyer": 0, "Charges": 1}

router = APIRouter(
    prefix="/me",
    tags=["Me"],
    dependencies=[Depends(get_current_user)],
)


async def _get_owner_for_user(db: AsyncSession, user: User) -> Owner | None:
    if user.ownerId is None:
        return None
    return await db.get(Owner, user.ownerId)


@router.get("/profile", response_model=ProfileRead)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    owner = await _get_owner_for_user(db, current_user)
    return ProfileRead(
        user=UserRead.model_validate(current_user),
        owner=OwnerRead.model_validate(owner) if owner else None,
    )


# ---------------------------------------------------------------------------
# Test email — simule exactement le cron, email envoyé au proprio (pas au locataire)
# ---------------------------------------------------------------------------

class TestEmailInput(BaseModel):
    tenant_id: int | None = None   # None = tous les locataires actifs du propriétaire
    month: str                     # "YYYY-MM"


class TestEmailResult(BaseModel):
    sent: list[str]      # locataires pour lesquels l'email a été envoyé au proprio
    skipped: list[dict]  # [{name, reason}] — case non cochée, pas d'email, erreur, etc.


@router.post(
    "/test-email",
    response_model=TestEmailResult,
    summary="Simuler le cron : crée la quittance si absente, génère le PDF et envoie l'avis si la case est cochée (email au proprio)",
)
async def send_test_email(
    payload: TestEmailInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestEmailResult:
    """
    Réplique exactement le comportement du cron pour le mois donné :
    - Crée la quittance (avis d'échéance) si elle n'existe pas encore.
    - Génère le PDF.
    - Envoie l'email si sendNoticeOfLeaseRental == 1 et que le locataire a un email.
    En mode test, l'email est envoyé à l'adresse du propriétaire (pas au locataire).
    """
    # --- Parse month ---
    try:
        year, month = (int(x) for x in payload.month.split("-"))
        _, last_day = calendar.monthrange(year, month)
    except (ValueError, AttributeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Format de mois invalide. Attendu : YYYY-MM")

    # --- Owner ---
    if current_user.ownerId is None and not current_user.isAdmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Aucun profil propriétaire associé")

    owner: Owner | None = None
    if current_user.ownerId is not None:
        owner = await db.get(Owner, current_user.ownerId)
    if owner is None and not current_user.isAdmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Profil propriétaire introuvable")
    if owner is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Compte administrateur sans profil propriétaire — impossible d'envoyer un email de test",
        )
    if not owner.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Le propriétaire n'a pas d'adresse email configurée")

    # --- Collect tenants ---
    if payload.tenant_id is not None:
        tenant = await db.get(Tenant, payload.tenant_id)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Locataire introuvable")
        if not current_user.isAdmin:
            unit = await db.get(PlacesUnit, tenant.placeUnitId) if tenant.placeUnitId else None
            place = await db.get(Place, unit.placeId) if unit else None
            if not place or place.ownerId != owner.id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Ce locataire n'appartient pas à votre portefeuille")
        tenants_to_process = [tenant]
    else:
        places = (await db.execute(select(Place).where(Place.ownerId == owner.id))).scalars().all()
        tenants_to_process: list[Tenant] = []
        for place in places:
            units = (await db.execute(select(PlacesUnit).where(PlacesUnit.placeId == place.id))).scalars().all()
            for unit in units:
                unit_tenants = (
                    await db.execute(
                        select(Tenant).where(Tenant.placeUnitId == unit.id, Tenant.active == 1)
                    )
                ).scalars().all()
                tenants_to_process.extend(unit_tenants)

    # --- Process each tenant (même logique que le cron) ---
    sent: list[str] = []
    skipped: list[dict] = []

    period_begin_dt = datetime(year, month, 1)
    period_end_dt = datetime(year, month, last_day)
    next_period_begin = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

    for tenant in tenants_to_process:
        label = " ".join(filter(None, [tenant.firstName, tenant.name])) or f"Tenant #{tenant.id}"

        # 1. Loyers actifs hors Garantie — même filtre que le cron
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
            skipped.append({"name": label, "reason": "Aucun loyer actif"})
            continue

        # Frais du mois (rentsFees) — même filtre que le cron
        fees = (
            await db.execute(
                select(RentsFee).where(
                    RentsFee.tenantId == tenant.id,
                    RentsFee.applicationMonth >= period_begin_dt,
                    RentsFee.applicationMonth <= period_end_dt,
                )
            )
        ).scalars().all()

        amount = sum(float(r.price or 0) for r in rents) + sum(float(f.price or 0) for f in fees)

        # 2. Idempotence — ne pas recréer si déjà présente (même logique que le cron)
        existing = (
            await db.execute(
                select(RentReceipt)
                .where(
                    RentReceipt.tenantId == tenant.id,
                    RentReceipt.periodBegin >= period_begin_dt,
                    RentReceipt.periodBegin < next_period_begin,
                )
                .limit(1)
            )
        ).scalars().first()

        receipt_created = False
        if existing is None:
            # 3. Créer la quittance + détails — identique au cron
            receipt = RentReceipt(
                tenantId=tenant.id,
                placeUnitId=tenant.placeUnitId,
                placeUnitRoomId=tenant.placeUnitRoomId,
                amount=amount,
                periodBegin=period_begin_dt,
                periodEnd=period_end_dt,
                paid=0,
            )
            db.add(receipt)
            await db.flush()

            sorted_rents = sorted(rents, key=lambda r: _RENT_TYPE_ORDER.get(r.type or "", 99))
            detail_order = 1
            for rent in sorted_rents:
                db.add(RentReceiptsDetail(
                    rentReceiptsId=receipt.id,
                    sortOrder=detail_order,
                    description=rent.type,
                    price=rent.price,
                ))
                detail_order += 1
            for fee in fees:
                db.add(RentReceiptsDetail(
                    rentReceiptsId=receipt.id,
                    sortOrder=detail_order,
                    description=fee.description,
                    price=fee.price,
                ))
                detail_order += 1
            await db.flush()
            receipt_created = True
        else:
            receipt = existing

        # 4. Générer le PDF (avis d'échéance) — identique au cron
        ctx = None
        pdf_bytes: bytes | None = None
        try:
            ctx = await get_receipt_context(db, receipt.id, doc_type_override="avis")
            FILES_DIR.mkdir(parents=True, exist_ok=True)
            file_path = FILES_DIR / ctx.filename
            if file_path.exists():
                pdf_bytes = file_path.read_bytes()
            else:
                pdf_bytes = generate_receipt_pdf(ctx, doc_type_override="avis")
                file_path.write_bytes(pdf_bytes)
            receipt.pdfFilename = ctx.filename
        except Exception as exc:
            if receipt_created:
                await db.rollback()
            skipped.append({"name": label, "reason": f"Erreur génération PDF : {exc}"})
            continue

        if receipt_created:
            await db.commit()

        # 5. Vérifier les conditions d'envoi — identique au cron
        receipt_info = "nouvelle quittance" if receipt_created else "quittance existante"

        # Envoyer si case cochée OU s'il y a des rentsFees dans la quittance
        should_send = bool(tenant.sendNoticeOfLeaseRental) or len(fees) > 0

        if not should_send:
            skipped.append({"name": label, "reason": f"Case 'avis d'échéance' non cochée et aucun frais ({receipt_info})"})
            continue

        if not tenant.email:
            skipped.append({"name": label, "reason": f"Pas d'email locataire ({receipt_info})"})
            continue

        # Collecter les justificatifs des rentsFees
        month_prefix = period_begin_dt.strftime("%Y-%m")
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

        # 6. Construire et envoyer l'email au proprio (mode test)
        period = receipt.periodBegin
        month_name = MONTHS_FR[period.month - 1]
        yr = period.year
        unit_friendly = ctx.unit_name or ctx.place_name
        subject = f"[TEST] Avis d'échéance - {unit_friendly}" if unit_friendly else "[TEST] Avis d'échéance"
        body = (
            f"[Email de test — destinataire réel : {label} <{tenant.email}>]\n\n"
            f"Bonjour,\n\n"
            f"Vous trouverez ci-joint l'avis d'échéance du mois de {month_name} {yr}.\n"
            f"Vous souhaitant bonne réception.\n\n"
            f"Bonne journée,\n"
            f"{owner.name}\n"
        )

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda _ctx=ctx, _pdf=pdf_bytes, _sub=subject, _body=body, _extra=extra_attachments: send_pdf_email_sync(
                    from_addr=owner.email,
                    from_name=owner.name or "",
                    to_addr=owner.email,
                    to_name=owner.name or "",
                    subject=_sub,
                    body=_body,
                    pdf_bytes=_pdf,
                    pdf_filename=_ctx.filename,
                    extra_attachments=_extra,
                ),
            )
            sent.append(f"{label} ({receipt_info})")
        except Exception as exc:
            skipped.append({"name": label, "reason": f"Erreur envoi email : {exc}"})

    return TestEmailResult(sent=sent, skipped=skipped)


@router.patch("/profile", response_model=ProfileRead)
async def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    # Update user fields (name, username only — email/password require separate flows)
    if payload.user:
        for k, v in payload.user.model_dump(exclude_unset=True).items():
            setattr(current_user, k, v)
        await db.commit()
        await db.refresh(current_user)

    # Update owner fields
    owner = await _get_owner_for_user(db, current_user)
    if payload.owner and owner:
        for k, v in payload.owner.model_dump(exclude_unset=True).items():
            setattr(owner, k, v)
        await db.commit()
        await db.refresh(owner)

    return ProfileRead(
        user=UserRead.model_validate(current_user),
        owner=OwnerRead.model_validate(owner) if owner else None,
    )

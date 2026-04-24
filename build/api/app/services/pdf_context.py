"""
PDF context — loads all data needed to generate a rental PDF document.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime, date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rentReceipt import RentReceipt
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.models.tenant import Tenant
from app.models.placesUnit import PlacesUnit
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.place import Place
from app.models.owner import Owner


@dataclass
class DetailLine:
    description: str
    price: float


@dataclass
class ReceiptContext:
    # ---- propriétaire ----
    owner_name: str
    owner_address: str
    owner_zip: str
    owner_city: str
    owner_phone: str
    owner_email: str
    owner_iban: str

    # ---- bien ----
    unit_address: str
    unit_zip: str
    unit_city: str
    unit_name: str
    place_name: str

    # ---- locataire ----
    tenant_civility: str          # "M.", "Mme", "Mlle", "Société" or ""
    tenant_fullname: str
    tenant_billing_address: str
    tenant_billing_zip: str
    tenant_billing_city: str

    # ---- quittance ----
    amount_total: float
    details: list[DetailLine]
    paid: bool
    is_garantie: bool             # True → quittance de garantie

    # ---- dates textuelles (dd/mm/yyyy) ----
    txt_date_from: str
    txt_date_to: str
    txt_date_payment: str         # withdrawDay clamped, same month as period
    txt_date_today: str           # date of PDF generation

    # ---- nom de fichier ----
    filename: str


def _fmt(dt: datetime | date | None) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    return dt.strftime("%d/%m/%Y")


def _civility(genre: str | None) -> str:
    mapping = {"M": "M.", "Mme": "Mme", "Mlle": "Mlle", "Societe": "Société"}
    return mapping.get(genre or "", "")


def _payment_date(period_begin: datetime | None, withdraw_day: int | None) -> str:
    """Return the due date: withdrawDay of the same month as period_begin, fallback day 6."""
    if period_begin is None:
        return ""
    day = withdraw_day if withdraw_day else 6
    _, last_day = calendar.monthrange(period_begin.year, period_begin.month)
    day = min(day, last_day)
    return f"{day:02d}/{period_begin.month:02d}/{period_begin.year:04d}"


def _sanitize(s: str | None) -> str:
    return (s or "").strip()


def _build_filename(
    unit_zip: str, place_name: str, unit_name: str,
    period_begin: datetime | None, doc_type: str,
) -> str:
    import re
    month = period_begin.strftime("%Y-%m") if period_begin else "0000-00"
    raw = f"{unit_zip}-{place_name}-{unit_name}.{month}.{doc_type}.pdf"
    return re.sub(r"\s+", "", raw)


async def get_receipt_context(
    db: AsyncSession,
    receipt_id: int,
    doc_type_override: str | None = None,
) -> ReceiptContext:
    """
    Load all data required to generate a PDF for a given rentReceipt.
    doc_type_override: "quittance" | "avis" | "garantie" | None (auto)
    """
    receipt = await db.get(RentReceipt, receipt_id)
    if not receipt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceipt not found")

    # Details ordered by sortOrder
    details_rows = (
        await db.execute(
            select(RentReceiptsDetail)
            .where(RentReceiptsDetail.rentReceiptsId == receipt_id)
            .order_by(RentReceiptsDetail.sortOrder)
        )
    ).scalars().all()

    # Always show Loyer then Charges first (at 0 if absent), same as old PHP logic
    loyer_line = DetailLine(description="Loyer", price=0.0)
    charges_line = DetailLine(description="Charges", price=0.0)
    extras: list[DetailLine] = []
    for d in details_rows:
        desc = _sanitize(d.description)
        price = float(d.price) if d.price is not None else 0.0
        if desc.lower() == "loyer":
            loyer_line = DetailLine(description=desc, price=price)
        elif desc.lower() == "charges":
            charges_line = DetailLine(description=desc, price=price)
        else:
            extras.append(DetailLine(description=desc, price=price))
    details = [loyer_line, charges_line] + extras

    # Consistency check: sum of detail lines must match receipt.amount
    details_sum = sum(float(d.price or 0) for d in details_rows)
    receipt_amount = float(receipt.amount) if receipt.amount is not None else 0.0
    if abs(details_sum - receipt_amount) > 0.01:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=(
                f"Incohérence des données : somme des lignes ({details_sum:.2f}€) "
                f"≠ montant de la quittance ({receipt_amount:.2f}€). "
                f"Supprimez la quittance et recréez-la."
            ),
        )

    # Detect garantie
    is_garantie = any("garantie" in (d.description or "").lower() for d in details_rows)
    if doc_type_override == "garantie":
        is_garantie = True

    # Tenant
    tenant = await db.get(Tenant, receipt.tenantId)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # PlacesUnit
    unit = await db.get(PlacesUnit, tenant.placeUnitId)
    if not unit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnit not found")

    # Place
    place = await db.get(Place, unit.placeId)
    if not place:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Owner
    owner = await db.get(Owner, place.ownerId)
    if not owner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner not found")

    # Unit name: use room name if flatshare, otherwise unit.name (same logic as old PHP)
    unit_name_for_file = _sanitize(unit.name or f"unit{unit.id}")
    if unit.flatshare and tenant.placeUnitRoomId:
        room = await db.get(PlacesUnitsRoom, tenant.placeUnitRoomId)
        if room and room.name:
            unit_name_for_file = _sanitize(room.name)

    # Billing address: use tenant billing if different, else unit address
    if tenant.billingSameAsRental:
        billing_address = _sanitize(unit.address)
        billing_zip = str(unit.zipCode or "")
        billing_city = _sanitize(unit.city)
    else:
        billing_address = _sanitize(tenant.billingAddress)
        billing_zip = str(tenant.billingZipCode or "")
        billing_city = _sanitize(tenant.billingCity)

    # Determine doc_type for filename
    if doc_type_override:
        doc_type = doc_type_override.capitalize()
    elif is_garantie:
        doc_type = "QuittanceGarantie"
    elif receipt.paid:
        doc_type = "QuittanceLoyer"
    else:
        doc_type = "AvisEcheance"

    filename = _build_filename(
        unit_zip=str(place.zipCode or ""),
        place_name=_sanitize(place.name),
        unit_name=unit_name_for_file,
        period_begin=receipt.periodBegin,
        doc_type=doc_type,
    )

    return ReceiptContext(
        owner_name=_sanitize(owner.name),
        owner_address=_sanitize(owner.address),
        owner_zip=str(owner.zipCode or ""),
        owner_city=_sanitize(owner.city),
        owner_phone=_sanitize(owner.phoneNumber),
        owner_email=_sanitize(owner.email),
        owner_iban=_sanitize(owner.iban),
        unit_address=_sanitize(unit.address or place.address),
        unit_zip=str(unit.zipCode or place.zipCode or ""),
        unit_city=_sanitize(unit.city or place.city),
        unit_name=_sanitize(unit.friendlyName or unit.name or ""),
        place_name=_sanitize(place.name),
        tenant_civility=_civility(tenant.genre),
        tenant_fullname=" ".join(filter(None, [tenant.firstName, tenant.name])),
        tenant_billing_address=billing_address,
        tenant_billing_zip=billing_zip,
        tenant_billing_city=billing_city,
        amount_total=float(receipt.amount) if receipt.amount is not None else 0.0,
        details=details,
        paid=bool(receipt.paid),
        is_garantie=is_garantie,
        txt_date_from=_fmt(receipt.periodBegin),
        txt_date_to=_fmt(receipt.periodEnd),
        txt_date_payment=_payment_date(receipt.periodBegin, tenant.withdrawDay),
        txt_date_today=datetime.now().strftime("%d/%m/%Y"),
        filename=filename,
    )

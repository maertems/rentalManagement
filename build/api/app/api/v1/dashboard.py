from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.models.owner import Owner
from app.models.place import Place
from app.models.placesUnit import PlacesUnit
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.tenant import Tenant
from app.models.rent import Rent
from app.models.rentReceipt import RentReceipt
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.schemas.dashboard import (
    OccupancyResponse,
    OccupancyPlace,
    OccupancyUnit,
    OccupancyRoom,
    OccupancyTenant,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


def _parse_month(month: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(month, "%Y-%m")
        return dt.year, dt.month
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid month format, expected YYYY-MM",
        )


@router.get("/occupancy", response_model=OccupancyResponse)
async def get_occupancy(
    month: str = Query(..., description="Target month as YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    year, mon = _parse_month(month)

    # -----------------------------------------------------------------------
    # Structure : places / units / rooms (scoped)
    # -----------------------------------------------------------------------
    places_stmt = select(Place).order_by(Place.name)
    if owner_ctx is not None:
        places_stmt = places_stmt.where(Place.ownerId == owner_ctx.id)
    places_rows = (await db.execute(places_stmt)).scalars().all()

    owners_rows = (await db.execute(select(Owner))).scalars().all()
    units_rows = (await db.execute(
        select(PlacesUnit).order_by(PlacesUnit.name)
    )).scalars().all()
    rooms_rows = (await db.execute(
        select(PlacesUnitsRoom).order_by(PlacesUnitsRoom.name)
    )).scalars().all()

    # -----------------------------------------------------------------------
    # Quittances du mois : source principale
    # Un rentReceipt porte son propre placeUnitId / placeUnitRoomId /
    # tenantId / amount / paid — c'est lui qui dit qui était où et à quel prix.
    # -----------------------------------------------------------------------
    month_receipts = (await db.execute(
        select(RentReceipt).where(
            and_(
                extract("year", RentReceipt.periodBegin) == year,
                extract("month", RentReceipt.periodBegin) == mon,
            )
        )
    )).scalars().all()

    # Exclure les quittances de garantie
    # 1. via warantyReceiptId des tenants (garanties "officielles")
    waranty_ids = {
        w for w in (await db.execute(
            select(Tenant.warantyReceiptId).where(Tenant.warantyReceiptId.isnot(None))
        )).scalars().all()
        if w is not None
    }
    # 2. via les détails contenant "garantie" (garanties sans lien warantyReceiptId)
    month_receipt_ids = [r.id for r in month_receipts]
    garantie_detail_ids: set[int] = set()
    if month_receipt_ids:
        garantie_detail_ids = {
            rid for rid in (await db.execute(
                select(RentReceiptsDetail.rentReceiptsId).where(
                    RentReceiptsDetail.rentReceiptsId.in_(month_receipt_ids),
                    func.lower(RentReceiptsDetail.description).contains("garantie"),
                )
            )).scalars().all()
            if rid is not None
        }
    month_receipts = [r for r in month_receipts if r.id not in waranty_ids and r.id not in garantie_detail_ids]

    # Un seul enregistrement par locataire (on cumule si plusieurs — cas rare)
    receipt_by_tenant: dict[int, RentReceipt] = {}
    for rec in month_receipts:
        if rec.tenantId is None:
            continue
        if rec.tenantId not in receipt_by_tenant:
            receipt_by_tenant[rec.tenantId] = rec
        else:
            # Cumuler le montant si plusieurs quittances pour le même locataire
            existing = receipt_by_tenant[rec.tenantId]
            if rec.amount is not None:
                existing.amount = (float(existing.amount or 0) + float(rec.amount))
            if rec.paid == 1:
                existing.paid = 1

    receipt_tenant_ids = set(receipt_by_tenant.keys())

    # -----------------------------------------------------------------------
    # Locataires référencés dans les quittances (peuvent être inactifs)
    # -----------------------------------------------------------------------
    tenants_from_receipts: list[Tenant] = []
    if receipt_tenant_ids:
        tenants_from_receipts = (await db.execute(
            select(Tenant).where(Tenant.id.in_(receipt_tenant_ids))
        )).scalars().all()

    # -----------------------------------------------------------------------
    # Locataires actifs SANS quittance ce mois → affichés avec montant estimé
    # (utile pour le mois courant avant génération des quittances)
    # -----------------------------------------------------------------------
    all_active_tenants = (await db.execute(
        select(Tenant).where(Tenant.active == 1)
    )).scalars().all()
    active_without_receipt = [t for t in all_active_tenants if t.id not in receipt_tenant_ids]

    # Montant de fallback : somme Loyer + Charges actifs
    rent_rows = (await db.execute(
        select(Rent).where(and_(Rent.type.in_(["Loyer", "Charges"]), Rent.active == 1))
    )).scalars().all()
    fallback_by_tenant: dict[int, float] = {}
    for r in rent_rows:
        if r.tenantId is not None and r.price is not None:
            fallback_by_tenant[r.tenantId] = (
                fallback_by_tenant.get(r.tenantId, 0.0) + float(r.price)
            )

    # -----------------------------------------------------------------------
    # Index
    # -----------------------------------------------------------------------
    ownerById = {o.id: o for o in owners_rows}

    unitsByPlaceId: dict[int, list[PlacesUnit]] = {}
    for u in units_rows:
        if u.placeId:
            unitsByPlaceId.setdefault(u.placeId, []).append(u)

    roomsByUnitId: dict[int, list[PlacesUnitsRoom]] = {}
    for r in rooms_rows:
        if r.placesUnitsId:
            roomsByUnitId.setdefault(r.placesUnitsId, []).append(r)

    tenant_by_id: dict[int, Tenant] = {t.id: t for t in tenants_from_receipts}
    for t in all_active_tenants:
        tenant_by_id[t.id] = t

    # -----------------------------------------------------------------------
    # Placement des locataires dans les logements pour CE mois :
    #   - Locataires avec quittance : utiliser placeUnitId/RoomId du receipt
    #     (représente le logement à l'époque, pas nécessairement l'actuel)
    #   - Locataires actifs sans quittance : utiliser placeUnitId du tenant
    # -----------------------------------------------------------------------
    tenantsByUnitId: dict[int, list[tuple[Tenant, RentReceipt | None]]] = {}
    tenantsByRoomId: dict[int, list[tuple[Tenant, RentReceipt | None]]] = {}

    for tid, rec in receipt_by_tenant.items():
        tenant = tenant_by_id.get(tid)
        if tenant is None:
            continue
        unit_id = rec.placeUnitId or tenant.placeUnitId
        room_id = rec.placeUnitRoomId or tenant.placeUnitRoomId
        if room_id is not None:
            tenantsByRoomId.setdefault(room_id, []).append((tenant, rec))
        elif unit_id is not None:
            tenantsByUnitId.setdefault(unit_id, []).append((tenant, rec))

    today = date.today()
    is_current_or_future = (year, mon) >= (today.year, today.month)
    if is_current_or_future:
        for t in active_without_receipt:
            if t.placeUnitRoomId is not None:
                tenantsByRoomId.setdefault(t.placeUnitRoomId, []).append((t, None))
            elif t.placeUnitId is not None:
                tenantsByUnitId.setdefault(t.placeUnitId, []).append((t, None))

    paid_tenant_ids: set[int] = {
        tid for tid, rec in receipt_by_tenant.items() if rec.paid == 1
    }

    # -----------------------------------------------------------------------
    # Construction de la réponse
    # -----------------------------------------------------------------------
    def _build_tenant(t: Tenant, rec: RentReceipt | None) -> OccupancyTenant:
        if rec is not None:
            amount = float(rec.amount) if rec.amount is not None else fallback_by_tenant.get(t.id)
            estimated = rec.amount is None
        else:
            amount = fallback_by_tenant.get(t.id)
            estimated = True
        return OccupancyTenant(
            tenantId=t.id,
            firstName=t.firstName,
            name=t.name,
            rentAmount=amount,
            rentAmountEstimated=estimated,
            rentPaid=t.id in paid_tenant_ids,
        )

    places: list[OccupancyPlace] = []
    for p in places_rows:
        owner = ownerById.get(p.ownerId) if p.ownerId else None
        units_out: list[OccupancyUnit] = []
        for u in unitsByPlaceId.get(p.id, []):
            is_flatshare = bool(u.flatshare)
            rooms_out: list[OccupancyRoom] = []
            tenants_out: list[OccupancyTenant] = []
            if is_flatshare:
                for r in roomsByUnitId.get(u.id, []):
                    room_tenants = [
                        _build_tenant(t, rec)
                        for t, rec in tenantsByRoomId.get(r.id, [])
                    ]
                    rooms_out.append(OccupancyRoom(
                        roomId=r.id,
                        roomName=r.name,
                        surfaceArea=float(r.surfaceArea) if r.surfaceArea is not None else None,
                        tenants=room_tenants,
                    ))
            else:
                tenants_out = [
                    _build_tenant(t, rec)
                    for t, rec in tenantsByUnitId.get(u.id, [])
                ]

            units_out.append(OccupancyUnit(
                unitId=u.id,
                unitName=u.name,
                friendlyName=u.friendlyName,
                level=u.level,
                flatshare=is_flatshare,
                rooms=rooms_out,
                tenants=tenants_out,
            ))

        places.append(OccupancyPlace(
            placeId=p.id,
            placeName=p.name,
            ownerId=p.ownerId,
            ownerName=owner.name if owner else None,
            units=units_out,
        ))

    return OccupancyResponse(month=f"{year:04d}-{mon:02d}", places=places)

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase, _apply_sort
from app.models.rentReceipt import RentReceipt
from app.models.placesUnit import PlacesUnit
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.tenant import Tenant
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.schemas.rentReceipt import RentReceiptCreate, RentReceiptUpdate, RentReceiptFilter
from app.services.relations import ensure_exists, ensure_no_children


class CRUDRentReceipt(CRUDBase[RentReceipt, RentReceiptCreate, RentReceiptUpdate]):
    async def create(self, db: AsyncSession, obj_in: RentReceiptCreate) -> RentReceipt:
        await ensure_exists(db, PlacesUnit, obj_in.placeUnitId, "placeUnitId")
        await ensure_exists(db, PlacesUnitsRoom, obj_in.placeUnitRoomId, "placeUnitRoomId")
        await ensure_exists(db, Tenant, obj_in.tenantId, "tenantId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: RentReceipt, obj_in: RentReceiptUpdate) -> RentReceipt:
        await ensure_exists(db, PlacesUnit, obj_in.placeUnitId, "placeUnitId")
        await ensure_exists(db, PlacesUnitsRoom, obj_in.placeUnitRoomId, "placeUnitRoomId")
        await ensure_exists(db, Tenant, obj_in.tenantId, "tenantId")
        return await super().update(db, db_obj, obj_in)

    async def delete_by_id(self, db: AsyncSession, id_: int) -> None:
        await ensure_no_children(db, Tenant, Tenant.warantyReceiptId, id_, "tenants (warantyReceiptId)")
        # Supprimer les détails en cascade avant le receipt
        details = (await db.execute(
            select(RentReceiptsDetail).where(RentReceiptsDetail.rentReceiptsId == id_)
        )).scalars().all()
        for d in details:
            await db.delete(d)
        await db.flush()
        await self.delete(db, id_)

    async def list_filtered(
        self,
        db: AsyncSession,
        f: RentReceiptFilter,
        scope_tenant_ids: list[int] | None = None,
    ):
        stmt = select(RentReceipt)
        conditions = []
        if scope_tenant_ids is not None:
            if not scope_tenant_ids:
                return [], 0
            conditions.append(RentReceipt.tenantId.in_(scope_tenant_ids))
        if f.tenantId is not None:
            conditions.append(RentReceipt.tenantId == f.tenantId)
        if f.placeUnitId is not None:
            conditions.append(RentReceipt.placeUnitId == f.placeUnitId)
        if f.paid is not None:
            conditions.append(RentReceipt.paid == f.paid)
        if f.periodBeginGte is not None:
            conditions.append(RentReceipt.periodBegin >= f.periodBeginGte)
        if f.periodBeginLte is not None:
            conditions.append(RentReceipt.periodBegin <= f.periodBeginLte)
        if f.periodEndGte is not None:
            conditions.append(RentReceipt.periodEnd >= f.periodEndGte)
        if f.periodEndLte is not None:
            conditions.append(RentReceipt.periodEnd <= f.periodEndLte)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = _apply_sort(stmt, RentReceipt, f.sort)
        stmt = stmt.limit(f.limit).offset(f.offset)
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total


crud_rent_receipt = CRUDRentReceipt(RentReceipt)

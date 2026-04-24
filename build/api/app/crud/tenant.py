from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.tenant import Tenant
from app.models.placesUnit import PlacesUnit
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.rentReceipt import RentReceipt
from app.models.rent import Rent
from app.models.rentsFee import RentsFee
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantFilter
from app.services.relations import ensure_exists, ensure_no_children


class CRUDTenant(CRUDBase[Tenant, TenantCreate, TenantUpdate]):
    async def create(self, db: AsyncSession, obj_in: TenantCreate) -> Tenant:
        await ensure_exists(db, PlacesUnit, obj_in.placeUnitId, "placeUnitId")
        await ensure_exists(db, PlacesUnitsRoom, obj_in.placeUnitRoomId, "placeUnitRoomId")
        await ensure_exists(db, RentReceipt, obj_in.warantyReceiptId, "warantyReceiptId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: Tenant, obj_in: TenantUpdate) -> Tenant:
        await ensure_exists(db, PlacesUnit, obj_in.placeUnitId, "placeUnitId")
        await ensure_exists(db, PlacesUnitsRoom, obj_in.placeUnitRoomId, "placeUnitRoomId")
        await ensure_exists(db, RentReceipt, obj_in.warantyReceiptId, "warantyReceiptId")
        return await super().update(db, db_obj, obj_in)

    async def delete_by_id(self, db: AsyncSession, id_: int) -> None:
        await ensure_no_children(db, Rent, Rent.tenantId, id_, "rents")
        await ensure_no_children(db, RentsFee, RentsFee.tenantId, id_, "rentsFees")
        await ensure_no_children(db, RentReceipt, RentReceipt.tenantId, id_, "rentReceipts")
        await self.delete(db, id_)

    async def list_filtered(
        self,
        db: AsyncSession,
        f: TenantFilter,
        scope_unit_ids: list[int] | None = None,
    ):
        from sqlalchemy import and_, func
        stmt = select(Tenant)
        conditions = []
        if scope_unit_ids is not None:
            if not scope_unit_ids:
                return [], 0
            conditions.append(Tenant.placeUnitId.in_(scope_unit_ids))
        if f.placeUnitId is not None:
            conditions.append(Tenant.placeUnitId == f.placeUnitId)
        if f.active is not None:
            conditions.append(Tenant.active == f.active)
        if f.genre is not None:
            conditions.append(Tenant.genre == f.genre)
        if f.name is not None:
            conditions.append(Tenant.name.ilike(f"%{f.name}%"))
        if f.email is not None:
            conditions.append(Tenant.email.ilike(f"%{f.email}%"))
        if f.dateEntranceGte is not None:
            conditions.append(Tenant.dateEntrance >= f.dateEntranceGte)
        if f.dateEntranceLte is not None:
            conditions.append(Tenant.dateEntrance <= f.dateEntranceLte)
        if f.dateExitGte is not None:
            conditions.append(Tenant.dateExit >= f.dateExitGte)
        if f.dateExitLte is not None:
            conditions.append(Tenant.dateExit <= f.dateExitLte)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        from app.crud.base import _apply_sort
        stmt = _apply_sort(stmt, Tenant, f.sort)
        stmt = stmt.limit(f.limit).offset(f.offset)
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total


crud_tenant = CRUDTenant(Tenant)

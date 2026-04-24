from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase, _apply_sort
from app.models.rentsFee import RentsFee
from app.models.tenant import Tenant
from app.schemas.rentsFee import RentsFeeCreate, RentsFeeUpdate, RentsFeeFilter
from app.services.relations import ensure_exists


class CRUDRentsFee(CRUDBase[RentsFee, RentsFeeCreate, RentsFeeUpdate]):
    async def create(self, db: AsyncSession, obj_in: RentsFeeCreate) -> RentsFee:
        await ensure_exists(db, Tenant, obj_in.tenantId, "tenantId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: RentsFee, obj_in: RentsFeeUpdate) -> RentsFee:
        await ensure_exists(db, Tenant, obj_in.tenantId, "tenantId")
        return await super().update(db, db_obj, obj_in)

    async def list_filtered(self, db: AsyncSession, f: RentsFeeFilter, scope_tenant_ids: list[int] | None = None):
        from sqlalchemy import func
        stmt = select(RentsFee)
        conditions = []
        if f.tenantId is not None:
            conditions.append(RentsFee.tenantId == f.tenantId)
        if f.applicationMonthGte is not None:
            conditions.append(RentsFee.applicationMonth >= f.applicationMonthGte)
        if f.applicationMonthLte is not None:
            conditions.append(RentsFee.applicationMonth <= f.applicationMonthLte)
        if f.description is not None:
            conditions.append(RentsFee.description.ilike(f"%{f.description}%"))
        if scope_tenant_ids is not None:
            if not scope_tenant_ids:
                return [], 0
            conditions.append(RentsFee.tenantId.in_(scope_tenant_ids))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = _apply_sort(stmt, RentsFee, f.sort)
        stmt = stmt.limit(f.limit).offset(f.offset)
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total


crud_rents_fee = CRUDRentsFee(RentsFee)

from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.rent import Rent
from app.models.tenant import Tenant
from app.schemas.rent import RentCreate, RentUpdate, RentFilter
from app.services.relations import ensure_exists


class CRUDRent(CRUDBase[Rent, RentCreate, RentUpdate]):
    async def create(self, db: AsyncSession, obj_in: RentCreate) -> Rent:
        await ensure_exists(db, Tenant, obj_in.tenantId, "tenantId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: Rent, obj_in: RentUpdate) -> Rent:
        await ensure_exists(db, Tenant, obj_in.tenantId, "tenantId")
        return await super().update(db, db_obj, obj_in)

    async def list_filtered(
        self,
        db: AsyncSession,
        f: RentFilter,
        scope_tenant_ids: list[int] | None = None,
    ):
        filters = {
            "tenantId": f.tenantId,
            "type": f.type,
            "active": f.active,
        }
        in_filters = {}
        if scope_tenant_ids is not None:
            in_filters["tenantId"] = scope_tenant_ids
        return await self.list(
            db, filters=filters, in_filters=in_filters,
            limit=f.limit, offset=f.offset, sort=f.sort,
        )


crud_rent = CRUDRent(Rent)

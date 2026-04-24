from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.rentReceiptsDetail import RentReceiptsDetail
from app.models.rentReceipt import RentReceipt
from app.schemas.rentReceiptsDetail import RentReceiptsDetailCreate, RentReceiptsDetailUpdate, RentReceiptsDetailFilter
from app.services.relations import ensure_exists


class CRUDRentReceiptsDetail(CRUDBase[RentReceiptsDetail, RentReceiptsDetailCreate, RentReceiptsDetailUpdate]):
    async def create(self, db: AsyncSession, obj_in: RentReceiptsDetailCreate) -> RentReceiptsDetail:
        await ensure_exists(db, RentReceipt, obj_in.rentReceiptsId, "rentReceiptsId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: RentReceiptsDetail, obj_in: RentReceiptsDetailUpdate) -> RentReceiptsDetail:
        await ensure_exists(db, RentReceipt, obj_in.rentReceiptsId, "rentReceiptsId")
        return await super().update(db, db_obj, obj_in)

    async def list_filtered(self, db: AsyncSession, f: RentReceiptsDetailFilter):
        filters = {"rentReceiptsId": f.rentReceiptsId}
        return await self.list(db, filters=filters, limit=f.limit, offset=f.offset, sort=f.sort)


crud_rent_receipts_detail = CRUDRentReceiptsDetail(RentReceiptsDetail)

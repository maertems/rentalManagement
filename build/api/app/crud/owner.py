from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.owner import Owner
from app.models.place import Place
from app.models.user import User
from app.schemas.owner import OwnerCreate, OwnerUpdate, OwnerFilter
from app.services.relations import ensure_exists, ensure_no_children


class CRUDOwner(CRUDBase[Owner, OwnerCreate, OwnerUpdate]):
    async def create(self, db: AsyncSession, obj_in: OwnerCreate) -> Owner:
        # userId is optional legacy field (PocketBase compat); no uniqueness constraint
        if obj_in.userId is not None:
            await ensure_exists(db, User, obj_in.userId, "userId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: Owner, obj_in: OwnerUpdate) -> Owner:
        if obj_in.userId is not None:
            await ensure_exists(db, User, obj_in.userId, "userId")
        return await super().update(db, db_obj, obj_in)

    async def delete_by_id(self, db: AsyncSession, id_: int) -> None:
        await ensure_no_children(db, Place, Place.ownerId, id_, "places")
        await self.delete(db, id_)

    async def list_filtered(self, db: AsyncSession, f: OwnerFilter):
        filters = {
            "userId": f.userId,
            "name": f.name,
            "email": f.email,
            "city": f.city,
            "zipCode": f.zipCode,
        }
        return await self.list(db, filters=filters, limit=f.limit, offset=f.offset, sort=f.sort)


crud_owner = CRUDOwner(Owner)

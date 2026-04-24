from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.place import Place
from app.models.owner import Owner
from app.models.placesUnit import PlacesUnit
from app.schemas.place import PlaceCreate, PlaceUpdate, PlaceFilter
from app.services.relations import ensure_exists, ensure_no_children


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    async def create(self, db: AsyncSession, obj_in: PlaceCreate) -> Place:
        await ensure_exists(db, Owner, obj_in.ownerId, "ownerId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: Place, obj_in: PlaceUpdate) -> Place:
        await ensure_exists(db, Owner, obj_in.ownerId, "ownerId")
        return await super().update(db, db_obj, obj_in)

    async def delete_by_id(self, db: AsyncSession, id_: int) -> None:
        await ensure_no_children(db, PlacesUnit, PlacesUnit.placeId, id_, "placesUnits")
        await self.delete(db, id_)

    async def list_filtered(self, db: AsyncSession, f: PlaceFilter):
        filters = {
            "ownerId": f.ownerId,
            "name": f.name,
            "city": f.city,
            "zipCode": f.zipCode,
        }
        return await self.list(db, filters=filters, limit=f.limit, offset=f.offset, sort=f.sort)


crud_place = CRUDPlace(Place)

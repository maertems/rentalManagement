from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.placesUnit import PlacesUnit
from app.models.place import Place
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.tenant import Tenant
from app.models.rentReceipt import RentReceipt
from app.schemas.placesUnit import PlacesUnitCreate, PlacesUnitUpdate, PlacesUnitFilter
from app.services.relations import ensure_exists, ensure_no_children


class CRUDPlacesUnit(CRUDBase[PlacesUnit, PlacesUnitCreate, PlacesUnitUpdate]):
    async def create(self, db: AsyncSession, obj_in: PlacesUnitCreate) -> PlacesUnit:
        await ensure_exists(db, Place, obj_in.placeId, "placeId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: PlacesUnit, obj_in: PlacesUnitUpdate) -> PlacesUnit:
        await ensure_exists(db, Place, obj_in.placeId, "placeId")
        return await super().update(db, db_obj, obj_in)

    async def delete_by_id(self, db: AsyncSession, id_: int) -> None:
        await ensure_no_children(db, PlacesUnitsRoom, PlacesUnitsRoom.placesUnitsId, id_, "placesUnitsRooms")
        await ensure_no_children(db, Tenant, Tenant.placeUnitId, id_, "tenants")
        await ensure_no_children(db, RentReceipt, RentReceipt.placeUnitId, id_, "rentReceipts")
        await self.delete(db, id_)

    async def list_filtered(
        self,
        db: AsyncSession,
        f: PlacesUnitFilter,
        scope_place_ids: list[int] | None = None,
    ):
        filters = {
            "placeId": f.placeId,
            "flatshare": f.flatshare,
            "city": f.city,
            "friendlyName": f.friendlyName,
        }
        in_filters = {}
        if scope_place_ids is not None:
            in_filters["placeId"] = scope_place_ids
        return await self.list(
            db, filters=filters, in_filters=in_filters,
            limit=f.limit, offset=f.offset, sort=f.sort,
        )


crud_places_unit = CRUDPlacesUnit(PlacesUnit)

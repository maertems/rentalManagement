from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.placesUnit import PlacesUnit
from app.models.tenant import Tenant
from app.models.rentReceipt import RentReceipt
from app.schemas.placesUnitsRoom import PlacesUnitsRoomCreate, PlacesUnitsRoomUpdate, PlacesUnitsRoomFilter
from app.services.relations import ensure_exists, ensure_no_children


class CRUDPlacesUnitsRoom(CRUDBase[PlacesUnitsRoom, PlacesUnitsRoomCreate, PlacesUnitsRoomUpdate]):
    async def create(self, db: AsyncSession, obj_in: PlacesUnitsRoomCreate) -> PlacesUnitsRoom:
        await ensure_exists(db, PlacesUnit, obj_in.placesUnitsId, "placesUnitsId")
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: PlacesUnitsRoom, obj_in: PlacesUnitsRoomUpdate) -> PlacesUnitsRoom:
        await ensure_exists(db, PlacesUnit, obj_in.placesUnitsId, "placesUnitsId")
        return await super().update(db, db_obj, obj_in)

    async def delete_by_id(self, db: AsyncSession, id_: int) -> None:
        await ensure_no_children(db, Tenant, Tenant.placeUnitRoomId, id_, "tenants")
        await ensure_no_children(db, RentReceipt, RentReceipt.placeUnitRoomId, id_, "rentReceipts")
        await self.delete(db, id_)

    async def list_filtered(
        self,
        db: AsyncSession,
        f: PlacesUnitsRoomFilter,
        scope_unit_ids: list[int] | None = None,
    ):
        filters = {
            "placesUnitsId": f.placesUnitsId,
            "name": f.name,
        }
        in_filters = {}
        if scope_unit_ids is not None:
            in_filters["placesUnitsId"] = scope_unit_ids
        return await self.list(
            db, filters=filters, in_filters=in_filters,
            limit=f.limit, offset=f.offset, sort=f.sort,
        )


crud_places_units_room = CRUDPlacesUnitsRoom(PlacesUnitsRoom)

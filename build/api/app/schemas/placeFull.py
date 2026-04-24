from pydantic import BaseModel

from app.schemas.place import PlaceCreate, PlaceRead
from app.schemas.placesUnit import PlacesUnitRead
from app.schemas.placesUnitsRoom import PlacesUnitsRoomRead


class RoomInput(BaseModel):
    name: str | None = None
    surfaceArea: float | None = None


class UnitInput(BaseModel):
    name: str | None = None
    level: str | None = None
    flatshare: int = 0
    address: str | None = None
    zipCode: int | None = None
    city: str | None = None
    surfaceArea: float | None = None
    friendlyName: str | None = None
    rooms: list[RoomInput] = []


class PlaceFullCreate(BaseModel):
    place: PlaceCreate
    units: list[UnitInput] = []


class UnitFullRead(PlacesUnitRead):
    rooms: list[PlacesUnitsRoomRead] = []


class PlaceFullRead(BaseModel):
    place: PlaceRead
    units: list[UnitFullRead] = []

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PlacesUnitsRoomBase(BaseModel):
    name: str | None = None
    surfaceArea: float | None = None
    placesUnitsId: int | None = None


class PlacesUnitsRoomCreate(PlacesUnitsRoomBase):
    pass


class PlacesUnitsRoomUpdate(PlacesUnitsRoomBase):
    pass


class PlacesUnitsRoomRead(PlacesUnitsRoomBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class PlacesUnitsRoomFilter(BaseModel):
    placesUnitsId: int | None = None
    name: str | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

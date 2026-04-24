from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PlacesUnitBase(BaseModel):
    name: str | None = None
    level: str | None = None
    flatshare: int | None = None
    address: str | None = None
    zipCode: int | None = None
    city: str | None = None
    surfaceArea: float | None = None
    placeId: int | None = None
    friendlyName: str | None = None


class PlacesUnitCreate(PlacesUnitBase):
    pass


class PlacesUnitUpdate(PlacesUnitBase):
    pass


class PlacesUnitRead(PlacesUnitBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class PlacesUnitFilter(BaseModel):
    placeId: int | None = None
    flatshare: int | None = None
    city: str | None = None
    friendlyName: str | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

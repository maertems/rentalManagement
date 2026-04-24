from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PlaceBase(BaseModel):
    name: str | None = None
    address: str | None = None
    zipCode: int | None = None
    city: str | None = None
    ownerId: int | None = None


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(PlaceBase):
    pass


class PlaceRead(PlaceBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class PlaceFilter(BaseModel):
    ownerId: int | None = None
    name: str | None = None
    city: str | None = None
    zipCode: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RentBase(BaseModel):
    tenantId: int | None = None
    type: Literal["Loyer", "Charges", "Garantie"] | None = None
    price: float | None = None
    dateExpiration: datetime | None = None
    active: int | None = None


class RentCreate(RentBase):
    pass


class RentUpdate(RentBase):
    pass


class RentRead(RentBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class RentFilter(BaseModel):
    tenantId: int | None = None
    type: str | None = None
    active: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

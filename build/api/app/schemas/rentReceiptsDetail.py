from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RentReceiptsDetailBase(BaseModel):
    rentReceiptsId: int | None = None
    sortOrder: int | None = None
    description: str | None = None
    price: float | None = None


class RentReceiptsDetailCreate(RentReceiptsDetailBase):
    pass


class RentReceiptsDetailUpdate(RentReceiptsDetailBase):
    pass


class RentReceiptsDetailRead(RentReceiptsDetailBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class RentReceiptsDetailFilter(BaseModel):
    rentReceiptsId: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

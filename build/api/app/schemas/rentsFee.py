from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RentsFeeBase(BaseModel):
    tenantId: int | None = None
    applicationMonth: datetime | None = None
    description: str | None = None
    subDescription: str | None = None
    price: float | None = None


class RentsFeeCreate(RentsFeeBase):
    pass


class RentsFeeUpdate(RentsFeeBase):
    pass


class RentsFeeRead(RentsFeeBase):
    id: int
    hasDocument: bool = False
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class RentsFeeFilter(BaseModel):
    tenantId: int | None = None
    applicationMonthGte: datetime | None = None
    applicationMonthLte: datetime | None = None
    description: str | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

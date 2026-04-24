from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RentReceiptBase(BaseModel):
    placeUnitId: int | None = None
    placeUnitRoomId: int | None = None
    tenantId: int | None = None
    amount: float | None = None
    periodBegin: datetime | None = None
    periodEnd: datetime | None = None
    paid: int | None = None


class RentReceiptCreate(RentReceiptBase):
    pass


class RentReceiptUpdate(RentReceiptBase):
    pass


class RentReceiptRead(RentReceiptBase):
    id: int
    pdfFilename: str | None = None
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class RentReceiptFilter(BaseModel):
    tenantId: int | None = None
    placeUnitId: int | None = None
    paid: int | None = None
    periodBeginGte: datetime | None = None
    periodBeginLte: datetime | None = None
    periodEndGte: datetime | None = None
    periodEndLte: datetime | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

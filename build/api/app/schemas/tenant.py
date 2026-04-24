from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TenantBase(BaseModel):
    genre: Literal["Mlle", "Mme", "M", "Societe"] | None = None
    firstName: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    billingSameAsRental: int | None = None
    billingAddress: str | None = None
    billingZipCode: int | None = None
    billingCity: str | None = None
    billingPhone: str | None = None
    withdrawName: str | None = None
    withdrawDay: int | None = Field(None, ge=1, le=31)
    placeUnitId: int | None = None
    placeUnitRoomId: int | None = None
    sendNoticeOfLeaseRental: int | None = None
    sendLeaseRental: int | None = None
    active: int | None = None
    dateEntrance: datetime | None = None
    dateExit: datetime | None = None
    warantyReceiptId: int | None = None


class TenantCreate(TenantBase):
    withdrawDay: int = Field(1, ge=1, le=31)


class TenantUpdate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class TenantFilter(BaseModel):
    placeUnitId: int | None = None
    active: int | None = None
    genre: str | None = None
    name: str | None = None
    email: str | None = None
    dateEntranceGte: datetime | None = None
    dateEntranceLte: datetime | None = None
    dateExitGte: datetime | None = None
    dateExitLte: datetime | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

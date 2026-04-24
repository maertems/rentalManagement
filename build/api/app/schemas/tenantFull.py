from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.tenant import TenantCreate, TenantRead
from app.schemas.rent import RentRead
from app.schemas.rentReceipt import RentReceiptRead


class RentFullInput(BaseModel):
    price: float


class RentsFullInput(BaseModel):
    loyer: RentFullInput
    charges: RentFullInput
    garantie: RentFullInput


class CautionReceiptInput(BaseModel):
    amount: float
    periodBegin: datetime | None = None
    paid: int = 1


class TenantFullCreate(BaseModel):
    tenant: TenantCreate
    rents: RentsFullInput
    cautionReceipt: CautionReceiptInput | None = None


class TenantFullRead(BaseModel):
    tenant: TenantRead
    rents: list[RentRead]
    cautionReceipt: RentReceiptRead | None = None
    model_config = ConfigDict(from_attributes=True)

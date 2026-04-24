from pydantic import BaseModel, ConfigDict


class OccupancyTenant(BaseModel):
    tenantId: int
    firstName: str | None = None
    name: str | None = None
    rentAmount: float | None = None
    rentAmountEstimated: bool = False  # True = fallback loyer+charges, no receipt yet
    rentPaid: bool = False
    model_config = ConfigDict(from_attributes=True)


class OccupancyRoom(BaseModel):
    roomId: int
    roomName: str | None = None
    surfaceArea: float | None = None
    tenants: list[OccupancyTenant] = []


class OccupancyUnit(BaseModel):
    unitId: int
    unitName: str | None = None
    friendlyName: str | None = None
    level: str | None = None
    flatshare: bool = False
    rooms: list[OccupancyRoom] = []
    tenants: list[OccupancyTenant] = []


class OccupancyPlace(BaseModel):
    placeId: int
    placeName: str | None = None
    ownerId: int | None = None
    ownerName: str | None = None
    units: list[OccupancyUnit] = []


class OccupancyResponse(BaseModel):
    month: str  # YYYY-MM
    places: list[OccupancyPlace] = []

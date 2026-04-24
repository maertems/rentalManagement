from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.user import UserCreate, UserRead


class OwnerBase(BaseModel):
    name: str | None = None
    email: str | None = None
    address: str | None = None
    zipCode: int | None = None
    city: str | None = None
    phoneNumber: str | None = None
    iban: str | None = None
    userId: int | None = None  # conservé pour compat import PocketBase


class OwnerCreate(OwnerBase):
    pass  # userId optionnel — la relation passe désormais par users.ownerId


class OwnerUpdate(OwnerBase):
    pass


class OwnerRead(OwnerBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class OwnerFilter(BaseModel):
    userId: int | None = None
    name: str | None = None
    email: str | None = None
    city: str | None = None
    zipCode: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None


# ---------------------------------------------------------------------------
# Aggregate: create owner atomically with a user (admin only)
# Deux modes mutuellement exclusifs :
#   - user + owner  → crée un nouvel utilisateur puis l'owner
#   - existingUserId + owner → crée l'owner et lie l'utilisateur existant
# ---------------------------------------------------------------------------

class OwnerFullCreate(BaseModel):
    user: UserCreate | None = None
    existingUserId: int | None = None
    owner: OwnerBase

    @model_validator(mode="after")
    def _check_user_xor_existing(self) -> "OwnerFullCreate":
        has_user = self.user is not None
        has_existing = self.existingUserId is not None
        if not has_user and not has_existing:
            raise ValueError("Fournir 'user' (nouveau) ou 'existingUserId' (existant)")
        if has_user and has_existing:
            raise ValueError("Fournir 'user' OU 'existingUserId', pas les deux")
        return self


class OwnerFullRead(BaseModel):
    user: UserRead
    owner: OwnerRead

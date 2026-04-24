from pydantic import BaseModel
from app.schemas.user import UserRead
from app.schemas.owner import OwnerRead


class ProfileRead(BaseModel):
    user: UserRead
    owner: OwnerRead | None = None


class ProfileUserUpdate(BaseModel):
    """Fields a user can update on their own account (no email/password/isAdmin)."""
    name: str | None = None
    username: str | None = None


class ProfileOwnerUpdate(BaseModel):
    """Fields an owner can update on their own profile (no userId reassignment)."""
    name: str | None = None
    email: str | None = None
    address: str | None = None
    zipCode: int | None = None
    city: str | None = None
    phoneNumber: str | None = None
    iban: str | None = None


class ProfileUpdate(BaseModel):
    user: ProfileUserUpdate | None = None
    owner: ProfileOwnerUpdate | None = None

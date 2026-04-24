from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: str | None = None
    username: str | None = None
    name: str | None = None
    avatar: str | None = None
    verified: int | None = None
    emailVisibility: int | None = None
    isAdmin: int | None = None
    isWithdraw: int | None = None
    ownerId: int | None = None  # owner associé (1 owner → N users)


class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class UserRead(UserBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)


class UserFilter(BaseModel):
    email: str | None = None
    username: str | None = None
    name: str | None = None
    verified: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        data = obj_in.model_dump(exclude_unset=True, exclude={"password"})
        data["passwordHash"] = hash_password(obj_in.password)
        obj = User(**data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        data = obj_in.model_dump(exclude_unset=True, exclude={"password"})
        if obj_in.password is not None:
            data["passwordHash"] = hash_password(obj_in.password)
        for k, v in data.items():
            setattr(db_obj, k, v)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


crud_user = CRUDUser(User)

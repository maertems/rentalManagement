from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def _apply_sort(stmt, model, sort: str | None):
    if not sort:
        return stmt
    for part in sort.split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("-"):
            col_name = part[1:]
            direction = desc
        else:
            col_name = part
            direction = asc
        col = getattr(model, col_name, None)
        if col is not None:
            stmt = stmt.order_by(direction(col))
    return stmt


class CRUDBase(Generic[ModelT, CreateT, UpdateT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    async def get(self, db: AsyncSession, id_: int) -> ModelT | None:
        return await db.get(self.model, id_)

    async def list(
        self,
        db: AsyncSession,
        *,
        filters: dict[str, Any] | None = None,
        in_filters: dict[str, list[int]] | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[ModelT], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                col = getattr(self.model, key, None)
                if col is None:
                    continue
                if isinstance(value, str):
                    stmt = stmt.where(col.ilike(f"%{value}%"))
                    count_stmt = count_stmt.where(col.ilike(f"%{value}%"))
                else:
                    stmt = stmt.where(col == value)
                    count_stmt = count_stmt.where(col == value)

        if in_filters:
            for key, values in in_filters.items():
                col = getattr(self.model, key, None)
                if col is not None:
                    if not values:
                        # Empty scope → no results
                        return [], 0
                    stmt = stmt.where(col.in_(values))
                    count_stmt = count_stmt.where(col.in_(values))

        total = (await db.execute(count_stmt)).scalar_one()
        stmt = _apply_sort(stmt, self.model, sort)
        stmt = stmt.limit(limit).offset(offset)
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total

    async def create(self, db: AsyncSession, obj_in: CreateT) -> ModelT:
        data = obj_in.model_dump(exclude_unset=True)
        obj = self.model(**data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
        self, db: AsyncSession, db_obj: ModelT, obj_in: UpdateT
    ) -> ModelT:
        for k, v in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, k, v)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id_: int) -> None:
        obj = await self.get(db, id_)
        if obj is not None:
            await db.delete(obj)
            await db.commit()

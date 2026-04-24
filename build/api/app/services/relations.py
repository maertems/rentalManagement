from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_exists(
    db: AsyncSession,
    Model: type,
    id_: int | None,
    field_name: str,
) -> None:
    if id_ is None:
        return
    obj = await db.get(Model, id_)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{field_name}={id_} does not reference an existing row",
        )


async def ensure_no_children(
    db: AsyncSession,
    Model: type,
    filter_col,
    value: int,
    label: str,
) -> None:
    exists = await db.scalar(
        select(Model.id).where(filter_col == value).limit(1)
    )
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: referenced by {label}",
        )

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.placesUnitsRoom import crud_places_units_room
from app.models.owner import Owner
from app.schemas.placesUnitsRoom import (
    PlacesUnitsRoomCreate, PlacesUnitsRoomUpdate, PlacesUnitsRoomRead, PlacesUnitsRoomFilter,
)
from app.services.scope import get_owner_unit_ids, assert_unit_scope

router = APIRouter(
    prefix="/placesUnitsRooms",
    tags=["PlacesUnitsRooms"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=PlacesUnitsRoomRead, status_code=status.HTTP_201_CREATED)
async def create_places_units_room(
    payload: PlacesUnitsRoomCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    await assert_unit_scope(db, owner_ctx, payload.placesUnitsId)
    return await crud_places_units_room.create(db, payload)


@router.get("/{id}", response_model=PlacesUnitsRoomRead)
async def get_places_units_room(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_places_units_room.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnitsRoom not found")
    await assert_unit_scope(db, owner_ctx, obj.placesUnitsId)
    return obj


@router.get("", response_model=list[PlacesUnitsRoomRead])
async def list_places_units_rooms(
    response: Response,
    f: PlacesUnitsRoomFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    scope_unit_ids = None
    if owner_ctx is not None:
        scope_unit_ids = await get_owner_unit_ids(db, owner_ctx.id)
    rows, total = await crud_places_units_room.list_filtered(db, f, scope_unit_ids=scope_unit_ids)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=PlacesUnitsRoomRead)
async def update_places_units_room(
    id: int,
    payload: PlacesUnitsRoomUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_places_units_room.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnitsRoom not found")
    await assert_unit_scope(db, owner_ctx, obj.placesUnitsId)
    if payload.placesUnitsId is not None:
        await assert_unit_scope(db, owner_ctx, payload.placesUnitsId)
    return await crud_places_units_room.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_places_units_room(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_places_units_room.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnitsRoom not found")
    await assert_unit_scope(db, owner_ctx, obj.placesUnitsId)
    await crud_places_units_room.delete_by_id(db, id)

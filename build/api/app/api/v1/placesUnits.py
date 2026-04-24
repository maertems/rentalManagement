from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.placesUnit import crud_places_unit
from app.models.owner import Owner
from app.schemas.placesUnit import PlacesUnitCreate, PlacesUnitUpdate, PlacesUnitRead, PlacesUnitFilter
from app.services.scope import get_owner_place_ids, assert_place_scope, assert_unit_scope

router = APIRouter(
    prefix="/placesUnits",
    tags=["PlacesUnits"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=PlacesUnitRead, status_code=status.HTTP_201_CREATED)
async def create_places_unit(
    payload: PlacesUnitCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    await assert_place_scope(db, owner_ctx, payload.placeId)
    return await crud_places_unit.create(db, payload)


@router.get("/{id}", response_model=PlacesUnitRead)
async def get_places_unit(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_places_unit.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnit not found")
    await assert_unit_scope(db, owner_ctx, obj.id)
    return obj


@router.get("", response_model=list[PlacesUnitRead])
async def list_places_units(
    response: Response,
    f: PlacesUnitFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    scope_place_ids = None
    if owner_ctx is not None:
        scope_place_ids = await get_owner_place_ids(db, owner_ctx.id)
    rows, total = await crud_places_unit.list_filtered(db, f, scope_place_ids=scope_place_ids)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=PlacesUnitRead)
async def update_places_unit(
    id: int,
    payload: PlacesUnitUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_places_unit.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnit not found")
    await assert_unit_scope(db, owner_ctx, obj.id)
    # Prevent moving unit to a place outside scope
    if payload.placeId is not None:
        await assert_place_scope(db, owner_ctx, payload.placeId)
    return await crud_places_unit.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_places_unit(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_places_unit.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PlacesUnit not found")
    await assert_unit_scope(db, owner_ctx, obj.id)
    await crud_places_unit.delete_by_id(db, id)

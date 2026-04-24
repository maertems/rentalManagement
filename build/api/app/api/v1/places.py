from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.place import crud_place
from app.models.place import Place
from app.models.placesUnit import PlacesUnit
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.owner import Owner
from app.schemas.place import PlaceCreate, PlaceUpdate, PlaceRead, PlaceFilter
from app.schemas.placeFull import PlaceFullCreate, PlaceFullRead, UnitFullRead
from app.services.relations import ensure_exists
from app.services.scope import assert_place_scope

router = APIRouter(
    prefix="/places",
    tags=["Places"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=PlaceRead, status_code=status.HTTP_201_CREATED)
async def create_place(
    payload: PlaceCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    if owner_ctx is not None:
        payload.ownerId = owner_ctx.id
    return await crud_place.create(db, payload)


@router.post(
    "/full",
    response_model=PlaceFullRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_place_full(
    payload: PlaceFullCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    """Atomically create a place + its units + rooms (for flatshare units)."""
    if owner_ctx is not None:
        payload.place.ownerId = owner_ctx.id
    await ensure_exists(db, Owner, payload.place.ownerId, "ownerId")

    place_data = payload.place.model_dump(exclude_unset=True)
    place = Place(**place_data)
    db.add(place)
    await db.flush()

    created_units: list[tuple[PlacesUnit, list[PlacesUnitsRoom]]] = []
    for unit_in in payload.units:
        unit = PlacesUnit(
            name=unit_in.name,
            level=unit_in.level,
            flatshare=unit_in.flatshare,
            address=unit_in.address,
            zipCode=unit_in.zipCode,
            city=unit_in.city,
            surfaceArea=unit_in.surfaceArea,
            friendlyName=unit_in.friendlyName,
            placeId=place.id,
        )
        db.add(unit)
        await db.flush()

        rooms: list[PlacesUnitsRoom] = []
        if unit_in.flatshare:
            for room_in in unit_in.rooms:
                room = PlacesUnitsRoom(
                    name=room_in.name,
                    surfaceArea=room_in.surfaceArea,
                    placesUnitsId=unit.id,
                )
                db.add(room)
                rooms.append(room)
            if rooms:
                await db.flush()

        created_units.append((unit, rooms))

    await db.commit()
    await db.refresh(place)
    for unit, rooms in created_units:
        await db.refresh(unit)
        for room in rooms:
            await db.refresh(room)

    units_out = [
        UnitFullRead.model_validate(
            {**unit.__dict__, "rooms": [room for room in rooms]},
            from_attributes=True,
        )
        for unit, rooms in created_units
    ]
    return PlaceFullRead(place=PlaceRead.model_validate(place), units=units_out)


@router.get("/{id}", response_model=PlaceRead)
async def get_place(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_place.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Place not found")
    await assert_place_scope(db, owner_ctx, obj.id)
    return obj


@router.get("", response_model=list[PlaceRead])
async def list_places(
    response: Response,
    f: PlaceFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    if owner_ctx is not None:
        f.ownerId = owner_ctx.id
    rows, total = await crud_place.list_filtered(db, f)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=PlaceRead)
async def update_place(
    id: int,
    payload: PlaceUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_place.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Place not found")
    await assert_place_scope(db, owner_ctx, obj.id)
    # Prevent reassigning to another owner
    if owner_ctx is not None and payload.ownerId is not None:
        payload.ownerId = owner_ctx.id
    return await crud_place.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_place.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Place not found")
    await assert_place_scope(db, owner_ctx, obj.id)
    await crud_place.delete_by_id(db, id)

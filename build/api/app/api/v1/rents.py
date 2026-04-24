from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.rent import crud_rent
from app.models.owner import Owner
from app.schemas.rent import RentCreate, RentUpdate, RentRead, RentFilter
from app.services.scope import get_owner_tenant_ids, assert_tenant_scope

router = APIRouter(
    prefix="/rents",
    tags=["Rents"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=RentRead, status_code=status.HTTP_201_CREATED)
async def create_rent(
    payload: RentCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    await assert_tenant_scope(db, owner_ctx, payload.tenantId)
    return await crud_rent.create(db, payload)


@router.get("/{id}", response_model=RentRead)
async def get_rent(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rent not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    return obj


@router.get("", response_model=list[RentRead])
async def list_rents(
    response: Response,
    f: RentFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    scope_tenant_ids = None
    if owner_ctx is not None:
        scope_tenant_ids = await get_owner_tenant_ids(db, owner_ctx.id)
    rows, total = await crud_rent.list_filtered(db, f, scope_tenant_ids=scope_tenant_ids)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=RentRead)
async def update_rent(
    id: int,
    payload: RentUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rent not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    return await crud_rent.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rent(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rent not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    await crud_rent.delete(db, id)

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.tenant import crud_tenant
from app.models.tenant import Tenant
from app.models.rent import Rent
from app.models.rentReceipt import RentReceipt
from app.models.placesUnit import PlacesUnit
from app.models.placesUnitsRoom import PlacesUnitsRoom
from app.models.owner import Owner
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantRead, TenantFilter
from app.schemas.rentReceipt import RentReceiptRead
from app.schemas.tenantFull import TenantFullCreate, TenantFullRead
from app.services.relations import ensure_exists
from app.services.scope import get_owner_unit_ids, assert_unit_scope, assert_tenant_scope

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    await assert_unit_scope(db, owner_ctx, payload.placeUnitId)
    return await crud_tenant.create(db, payload)


@router.post(
    "/full",
    response_model=TenantFullRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant_full(
    payload: TenantFullCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    """Atomically create a tenant + 3 rents (Loyer / Charges / Garantie) + optional caution receipt."""
    await assert_unit_scope(db, owner_ctx, payload.tenant.placeUnitId)
    await ensure_exists(db, PlacesUnit, payload.tenant.placeUnitId, "placeUnitId")
    await ensure_exists(db, PlacesUnitsRoom, payload.tenant.placeUnitRoomId, "placeUnitRoomId")

    tenant_data = payload.tenant.model_dump(exclude_unset=True)
    tenant_data.pop("warantyReceiptId", None)
    tenant = Tenant(**tenant_data)
    db.add(tenant)
    await db.flush()

    rents: list[Rent] = []
    rents_spec = [
        ("Loyer", payload.rents.loyer.price),
        ("Charges", payload.rents.charges.price),
        ("Garantie", payload.rents.garantie.price),
    ]
    for rent_type, price in rents_spec:
        r = Rent(tenantId=tenant.id, type=rent_type, price=price, active=1)
        db.add(r)
        rents.append(r)
    await db.flush()

    caution_receipt: RentReceipt | None = None
    if payload.cautionReceipt is not None:
        caution_receipt = RentReceipt(
            tenantId=tenant.id,
            placeUnitId=payload.tenant.placeUnitId,
            placeUnitRoomId=payload.tenant.placeUnitRoomId,
            amount=payload.cautionReceipt.amount,
            periodBegin=payload.cautionReceipt.periodBegin,
            paid=payload.cautionReceipt.paid,
        )
        db.add(caution_receipt)
        await db.flush()
        tenant.warantyReceiptId = caution_receipt.id

    await db.commit()
    await db.refresh(tenant)
    for r in rents:
        await db.refresh(r)
    if caution_receipt is not None:
        await db.refresh(caution_receipt)

    return TenantFullRead(
        tenant=TenantRead.model_validate(tenant),
        rents=rents,
        cautionReceipt=caution_receipt,
    )


@router.get("/{id}", response_model=TenantRead)
async def get_tenant(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_tenant.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    await assert_tenant_scope(db, owner_ctx, obj.id)
    return obj


@router.get("/{id}/receipts", response_model=list[RentReceiptRead])
async def list_tenant_receipts(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    """All RentReceipts linked to a tenant, most recent first."""
    obj = await crud_tenant.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    await assert_tenant_scope(db, owner_ctx, obj.id)
    rows = (
        await db.execute(
            select(RentReceipt)
            .where(RentReceipt.tenantId == id)
            .order_by(RentReceipt.periodBegin.desc())
        )
    ).scalars().all()
    return rows


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    response: Response,
    f: TenantFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    scope_unit_ids = None
    if owner_ctx is not None:
        scope_unit_ids = await get_owner_unit_ids(db, owner_ctx.id)
    rows, total = await crud_tenant.list_filtered(db, f, scope_unit_ids=scope_unit_ids)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=TenantRead)
async def update_tenant(
    id: int,
    payload: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_tenant.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    await assert_tenant_scope(db, owner_ctx, obj.id)
    if payload.placeUnitId is not None:
        await assert_unit_scope(db, owner_ctx, payload.placeUnitId)
    return await crud_tenant.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_tenant.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    await assert_tenant_scope(db, owner_ctx, obj.id)
    await crud_tenant.delete_by_id(db, id)

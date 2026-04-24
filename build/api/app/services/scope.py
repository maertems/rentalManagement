"""
Scope helpers for owner-based data isolation.

All helpers accept `owner_ctx: Owner | None`.
  - None  → current user is admin → no restriction applied.
  - Owner → restrict to resources belonging to that owner.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Owner
from app.models.place import Place
from app.models.placesUnit import PlacesUnit
from app.models.tenant import Tenant


# ---------------------------------------------------------------------------
# ID-set helpers (used for IN-filter on list endpoints)
# ---------------------------------------------------------------------------

async def get_owner_place_ids(db: AsyncSession, owner_id: int) -> list[int]:
    rows = (
        await db.execute(select(Place.id).where(Place.ownerId == owner_id))
    ).scalars().all()
    return list(rows)


async def get_owner_unit_ids(db: AsyncSession, owner_id: int) -> list[int]:
    place_ids = await get_owner_place_ids(db, owner_id)
    if not place_ids:
        return []
    rows = (
        await db.execute(
            select(PlacesUnit.id).where(PlacesUnit.placeId.in_(place_ids))
        )
    ).scalars().all()
    return list(rows)


async def get_owner_tenant_ids(db: AsyncSession, owner_id: int) -> list[int]:
    unit_ids = await get_owner_unit_ids(db, owner_id)
    if not unit_ids:
        return []
    rows = (
        await db.execute(
            select(Tenant.id).where(Tenant.placeUnitId.in_(unit_ids))
        )
    ).scalars().all()
    return list(rows)


# ---------------------------------------------------------------------------
# Write-protection assertions (used for mutation endpoints)
# ---------------------------------------------------------------------------

def _deny() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: resource belongs to another owner",
    )


async def assert_place_scope(
    db: AsyncSession,
    owner_ctx: Owner | None,
    place_id: int | None,
) -> None:
    """Verify that place_id belongs to owner_ctx (no-op for admin or None place_id)."""
    if owner_ctx is None or place_id is None:
        return
    place = await db.get(Place, place_id)
    if place is None or place.ownerId != owner_ctx.id:
        _deny()


async def assert_unit_scope(
    db: AsyncSession,
    owner_ctx: Owner | None,
    unit_id: int | None,
) -> None:
    """Verify that the unit's parent place belongs to owner_ctx."""
    if owner_ctx is None or unit_id is None:
        return
    unit = await db.get(PlacesUnit, unit_id)
    if unit is None:
        return  # will 422 downstream via ensure_exists
    await assert_place_scope(db, owner_ctx, unit.placeId)


async def assert_tenant_scope(
    db: AsyncSession,
    owner_ctx: Owner | None,
    tenant_id: int | None,
) -> None:
    """Verify that the tenant's placeUnit belongs to owner_ctx."""
    if owner_ctx is None or tenant_id is None:
        return
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        return  # will 422 downstream via ensure_exists
    await assert_unit_scope(db, owner_ctx, tenant.placeUnitId)

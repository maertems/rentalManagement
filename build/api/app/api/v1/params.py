from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_admin_user, get_owner_context
from app.models.owner import Owner
from app.models.user import User
from app.services.params import get_owner_params, set_owner_params, get_all_params

router = APIRouter(
    prefix="/params",
    tags=["Params"],
    dependencies=[Depends(get_current_user)],
)


class OwnerParams(BaseModel):
    rentReceiptDay: int | None = Field(None, ge=1, le=31, description="Jour du mois pour la génération des quittances")


class OwnerParamsRead(BaseModel):
    ownerId: int
    rentReceiptDay: int | None = None


# ---------------------------------------------------------------------------
# GET /params/{owner_id}
# ---------------------------------------------------------------------------

@router.get("/{owner_id}", response_model=OwnerParamsRead)
async def read_params(
    owner_id: int,
    current_user: User = Depends(get_current_user),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    # Non-admin : ne peut accéder qu'à ses propres params
    if not current_user.isAdmin:
        if owner_ctx is None or owner_ctx.id != owner_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    p = get_owner_params(owner_id)
    return OwnerParamsRead(
        ownerId=owner_id,
        rentReceiptDay=p.get("rentReceiptDay"),
    )


# ---------------------------------------------------------------------------
# PATCH /params/{owner_id}
# ---------------------------------------------------------------------------

@router.patch("/{owner_id}", response_model=OwnerParamsRead)
async def update_params(
    owner_id: int,
    body: OwnerParams,
    current_user: User = Depends(get_current_user),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    # Non-admin : ne peut modifier que ses propres params
    if not current_user.isAdmin:
        if owner_ctx is None or owner_ctx.id != owner_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    updated = set_owner_params(owner_id, body.model_dump(exclude_none=True))
    return OwnerParamsRead(
        ownerId=owner_id,
        rentReceiptDay=updated.get("rentReceiptDay"),
    )


# ---------------------------------------------------------------------------
# GET /params  (admin uniquement — tous les propriétaires)
# ---------------------------------------------------------------------------

@router.get("", response_model=list[OwnerParamsRead])
async def read_all_params(
    _: User = Depends(get_admin_user),
):
    all_p = get_all_params()
    return [
        OwnerParamsRead(ownerId=int(oid), rentReceiptDay=p.get("rentReceiptDay"))
        for oid, p in all_p.items()
    ]

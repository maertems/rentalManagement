from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.api.deps import get_current_user, get_admin_user, get_owner_context
from app.crud.owner import crud_owner
from app.crud.user import crud_user
from app.models.owner import Owner
from app.models.user import User
from app.schemas.owner import (
    OwnerCreate, OwnerUpdate, OwnerRead, OwnerFilter,
    OwnerFullCreate, OwnerFullRead,
)
from app.schemas.user import UserRead

router = APIRouter(
    prefix="/owners",
    tags=["Owners"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Read endpoints — scoped by owner_ctx
# ---------------------------------------------------------------------------

@router.get("/{id}", response_model=OwnerRead)
async def get_owner(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_owner.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner not found")
    if owner_ctx is not None and obj.id != owner_ctx.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied")
    return obj


@router.get("", response_model=list[OwnerRead])
async def list_owners(
    response: Response,
    f: OwnerFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    if owner_ctx is not None:
        # Non-admin: renvoie uniquement son propre owner
        response.headers["X-Total-Count"] = "1"
        return [owner_ctx]
    rows, total = await crud_owner.list_filtered(db, f)
    response.headers["X-Total-Count"] = str(total)
    return rows


# ---------------------------------------------------------------------------
# Write endpoints — admin only
# ---------------------------------------------------------------------------

@router.post("", response_model=OwnerRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(get_admin_user)])
async def create_owner(payload: OwnerCreate, db: AsyncSession = Depends(get_db)):
    return await crud_owner.create(db, payload)


@router.post(
    "/full",
    response_model=OwnerFullRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
async def create_owner_full(
    payload: OwnerFullCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Crée un owner + lie un utilisateur, en une seule transaction (admin only).

    Mode A — nouveau user (payload.user fourni) :
      Crée l'user, crée l'owner, définit user.ownerId = owner.id.

    Mode B — user existant (payload.existingUserId fourni) :
      Vérifie que le user existe et n'a pas déjà un owner,
      crée l'owner, définit user.ownerId = owner.id.
    """
    # ------------------------------------------------------------------
    # Mode B : lier un user existant
    # ------------------------------------------------------------------
    if payload.existingUserId is not None:
        user = await db.get(User, payload.existingUserId)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.ownerId is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="This user is already linked to an owner",
            )

        owner_data = payload.owner.model_dump(exclude_unset=True)
        owner = Owner(**owner_data)
        db.add(owner)
        await db.flush()

        user.ownerId = owner.id
        await db.commit()
        await db.refresh(user)
        await db.refresh(owner)

    # ------------------------------------------------------------------
    # Mode A : créer un nouvel utilisateur
    # ------------------------------------------------------------------
    else:
        existing = await crud_user.get_by_email(db, payload.user.email)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
        if payload.user.username:
            existing_u = await crud_user.get_by_username(db, payload.user.username)
            if existing_u:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")

        user_data = payload.user.model_dump(exclude_unset=True, exclude={"password"})
        user_data["passwordHash"] = hash_password(payload.user.password)
        user = User(**user_data)
        db.add(user)
        await db.flush()

        owner_data = payload.owner.model_dump(exclude_unset=True)
        owner = Owner(**owner_data)
        db.add(owner)
        await db.flush()

        user.ownerId = owner.id
        await db.commit()
        await db.refresh(user)
        await db.refresh(owner)

    return OwnerFullRead(
        user=UserRead.model_validate(user),
        owner=OwnerRead.model_validate(owner),
    )


@router.patch("/{id}", response_model=OwnerRead, dependencies=[Depends(get_admin_user)])
async def update_owner(id: int, payload: OwnerUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_owner.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner not found")
    return await crud_owner.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(get_admin_user)])
async def delete_owner(id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_owner.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner not found")
    await crud_owner.delete_by_id(db, id)

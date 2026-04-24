from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.crud.user import crud_user
from app.schemas.user import UserCreate, UserUpdate, UserRead, UserFilter
from app.models.user import User

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await crud_user.get_by_email(db, payload.email)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    if payload.username:
        existing_u = await crud_user.get_by_username(db, payload.username)
        if existing_u:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    return await crud_user.create(db, payload)


@router.get("/{id}", response_model=UserRead)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_user.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return obj


@router.get("", response_model=list[UserRead])
async def list_users(
    response: Response,
    f: UserFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.isAdmin:
        # Non-admin: return only their own account
        response.headers["X-Total-Count"] = "1"
        return [current_user]
    filters = {"email": f.email, "username": f.username, "name": f.name, "verified": f.verified}
    rows, total = await crud_user.list(db, filters=filters, limit=f.limit, offset=f.offset, sort=f.sort)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch(
    "/{id}",
    response_model=UserRead,
    dependencies=[Depends(get_admin_user)],
)
async def update_user(id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_user.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return await crud_user.update(db, obj, payload)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
async def delete_user(id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_user.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    await crud_user.delete(db, id)

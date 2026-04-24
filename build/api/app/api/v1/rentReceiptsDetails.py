from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.crud.rentReceiptsDetail import crud_rent_receipts_detail
from app.schemas.rentReceiptsDetail import RentReceiptsDetailCreate, RentReceiptsDetailUpdate, RentReceiptsDetailRead, RentReceiptsDetailFilter

router = APIRouter(
    prefix="/rentReceiptsDetails",
    tags=["RentReceiptsDetails"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=RentReceiptsDetailRead, status_code=status.HTTP_201_CREATED)
async def create_rent_receipts_detail(payload: RentReceiptsDetailCreate, db: AsyncSession = Depends(get_db)):
    return await crud_rent_receipts_detail.create(db, payload)


@router.get("/{id}", response_model=RentReceiptsDetailRead)
async def get_rent_receipts_detail(id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_rent_receipts_detail.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceiptsDetail not found")
    return obj


@router.get("", response_model=list[RentReceiptsDetailRead])
async def list_rent_receipts_details(
    response: Response,
    f: RentReceiptsDetailFilter = Depends(),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await crud_rent_receipts_detail.list_filtered(db, f)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=RentReceiptsDetailRead)
async def update_rent_receipts_detail(id: int, payload: RentReceiptsDetailUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_rent_receipts_detail.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceiptsDetail not found")
    return await crud_rent_receipts_detail.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rent_receipts_detail(id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_rent_receipts_detail.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceiptsDetail not found")
    await crud_rent_receipts_detail.delete(db, id)

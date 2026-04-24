from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.rentsFee import crud_rents_fee
from app.models.owner import Owner
from app.schemas.rentsFee import RentsFeeCreate, RentsFeeUpdate, RentsFeeRead, RentsFeeFilter
from app.services.scope import get_owner_tenant_ids, assert_tenant_scope

FEES_DIR = Path("/app/files/fees")

router = APIRouter(
    prefix="/rentsFees",
    tags=["RentsFees"],
    dependencies=[Depends(get_current_user)],
)


def _doc_path(fee_id: int) -> Path | None:
    """Retourne le chemin du justificatif s'il existe, sinon None."""
    if not FEES_DIR.exists():
        return None
    for p in FEES_DIR.glob(f"{fee_id}.*"):
        return p
    return None


def _with_doc(fee, fee_id: int) -> RentsFeeRead:
    obj = RentsFeeRead.model_validate(fee)
    obj.hasDocument = _doc_path(fee_id) is not None
    return obj


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=RentsFeeRead, status_code=status.HTTP_201_CREATED)
async def create_rents_fee(
    payload: RentsFeeCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    if payload.tenantId:
        await assert_tenant_scope(db, owner_ctx, payload.tenantId)
    obj = await crud_rents_fee.create(db, payload)
    return _with_doc(obj, obj.id)


@router.get("/{id}", response_model=RentsFeeRead)
async def get_rents_fee(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rents_fee.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentsFee not found")
    if obj.tenantId:
        await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    return _with_doc(obj, obj.id)


@router.get("", response_model=list[RentsFeeRead])
async def list_rents_fees(
    response: Response,
    f: RentsFeeFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    scope_tenant_ids = None
    if owner_ctx is not None:
        scope_tenant_ids = await get_owner_tenant_ids(db, owner_ctx.id)
    rows, total = await crud_rents_fee.list_filtered(db, f, scope_tenant_ids=scope_tenant_ids)
    response.headers["X-Total-Count"] = str(total)
    return [_with_doc(r, r.id) for r in rows]


@router.patch("/{id}", response_model=RentsFeeRead)
async def update_rents_fee(
    id: int,
    payload: RentsFeeUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rents_fee.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentsFee not found")
    if obj.tenantId:
        await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    updated = await crud_rents_fee.update(db, obj, payload)
    return _with_doc(updated, updated.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rents_fee(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rents_fee.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentsFee not found")
    if obj.tenantId:
        await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    # Supprimer le justificatif associé si présent
    doc = _doc_path(id)
    if doc:
        doc.unlink(missing_ok=True)
    await crud_rents_fee.delete(db, id)


# ---------------------------------------------------------------------------
# Justificatif (document)
# ---------------------------------------------------------------------------

@router.post(
    "/{id}/document",
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un justificatif pour un frais",
)
async def upload_document(
    id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rents_fee.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentsFee not found")
    if obj.tenantId:
        await assert_tenant_scope(db, owner_ctx, obj.tenantId)

    FEES_DIR.mkdir(parents=True, exist_ok=True)

    # Supprimer l'ancien justificatif s'il existe
    old = _doc_path(id)
    if old:
        old.unlink(missing_ok=True)

    suffix = Path(file.filename or "file").suffix or ".bin"
    dest = FEES_DIR / f"{id}{suffix}"
    dest.write_bytes(await file.read())

    return {"filename": dest.name}


@router.get(
    "/{id}/document",
    summary="Télécharger le justificatif d'un frais",
)
async def download_document(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rents_fee.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentsFee not found")
    if obj.tenantId:
        await assert_tenant_scope(db, owner_ctx, obj.tenantId)

    doc = _doc_path(id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No document for this fee")

    return FileResponse(path=str(doc), filename=doc.name)


@router.delete(
    "/{id}/document",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer le justificatif d'un frais",
)
async def delete_document(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rents_fee.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentsFee not found")
    if obj.tenantId:
        await assert_tenant_scope(db, owner_ctx, obj.tenantId)

    doc = _doc_path(id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No document for this fee")
    doc.unlink(missing_ok=True)

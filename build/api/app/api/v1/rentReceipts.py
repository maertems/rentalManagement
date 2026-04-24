from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.rentReceipt import crud_rent_receipt
from app.models.owner import Owner
from app.schemas.rentReceipt import (
    RentReceiptCreate, RentReceiptUpdate, RentReceiptRead, RentReceiptFilter,
)
from app.services.scope import get_owner_tenant_ids, assert_tenant_scope
from app.services.pdf_context import get_receipt_context
from app.services.pdf_generator import generate_receipt_pdf

FILES_DIR = Path("/app/files")

router = APIRouter(
    prefix="/rentReceipts",
    tags=["RentReceipts"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=RentReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_rent_receipt(
    payload: RentReceiptCreate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    await assert_tenant_scope(db, owner_ctx, payload.tenantId)
    return await crud_rent_receipt.create(db, payload)


@router.get("/{id}", response_model=RentReceiptRead)
async def get_rent_receipt(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent_receipt.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceipt not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    return obj


@router.get("", response_model=list[RentReceiptRead])
async def list_rent_receipts(
    response: Response,
    f: RentReceiptFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    scope_tenant_ids = None
    if owner_ctx is not None:
        scope_tenant_ids = await get_owner_tenant_ids(db, owner_ctx.id)
    rows, total = await crud_rent_receipt.list_filtered(db, f, scope_tenant_ids=scope_tenant_ids)
    response.headers["X-Total-Count"] = str(total)
    return rows


@router.patch("/{id}", response_model=RentReceiptRead)
async def update_rent_receipt(
    id: int,
    payload: RentReceiptUpdate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent_receipt.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceipt not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    return await crud_rent_receipt.update(db, obj, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rent_receipt(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent_receipt.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceipt not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)
    await crud_rent_receipt.delete_by_id(db, id)


# ---------------------------------------------------------------------------
# PDF endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{id}/pdf",
    status_code=status.HTTP_201_CREATED,
    summary="Générer le PDF d'une quittance (immuable une fois créé)",
)
async def generate_pdf(
    id: int,
    doc_type: str | None = Query(
        default=None,
        description="Forcer le type : quittance | avis | garantie (auto-détecté par défaut)",
    ),
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent_receipt.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceipt not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)

    ctx = await get_receipt_context(db, id, doc_type_override=doc_type)

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = FILES_DIR / ctx.filename

    if file_path.exists():
        if obj.pdfFilename == ctx.filename:
            # Already generated and linked — idempotent, just return
            return {"filename": ctx.filename, "path": f"/files/{ctx.filename}"}
        # File exists on disk but not linked to this receipt (orphan from deleted receipt).
        # Re-link without regenerating.
        obj.pdfFilename = ctx.filename
        await db.commit()
        return {"filename": ctx.filename, "path": f"/files/{ctx.filename}"}

    pdf_bytes = generate_receipt_pdf(ctx, doc_type_override=doc_type)
    file_path.write_bytes(pdf_bytes)

    # Persist the filename so GET /pdf can find it unambiguously
    obj.pdfFilename = ctx.filename
    await db.commit()

    return {"filename": ctx.filename, "path": f"/files/{ctx.filename}"}


@router.get(
    "/{id}/pdf",
    summary="Télécharger le PDF d'une quittance (doit avoir été généré via POST au préalable)",
)
async def download_pdf(
    id: int,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    obj = await crud_rent_receipt.get(db, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RentReceipt not found")
    await assert_tenant_scope(db, owner_ctx, obj.tenantId)

    if not obj.pdfFilename:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="PDF not generated yet. Call POST /{id}/pdf first.",
        )

    file_path = FILES_DIR / obj.pdfFilename
    if not file_path.exists():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"PDF file missing on disk: {obj.pdfFilename}",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=obj.pdfFilename,
    )

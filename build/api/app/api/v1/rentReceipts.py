from datetime import date
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_owner_context
from app.crud.rentReceipt import crud_rent_receipt
from app.models.owner import Owner
from app.models.placesUnit import PlacesUnit
from app.models.tenant import Tenant
from app.schemas.rentReceipt import (
    RentReceiptCreate, RentReceiptUpdate, RentReceiptRead, RentReceiptFilter,
    RentReceiptGenerate,
)
from app.services.scope import get_owner_tenant_ids, assert_tenant_scope
from app.services.pdf_context import get_receipt_context
from app.services.pdf_generator import generate_receipt_pdf
from app.services.email import send_pdf_email_sync
from app.services.cron import (
    NoActiveRentError, ReceiptAlreadyExistsError, create_receipt_entry,
)

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

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


@router.post(
    "/generate",
    response_model=RentReceiptRead,
    status_code=status.HTTP_201_CREATED,
    summary="Générer l'entrée en base d'une quittance pour un locataire et un mois",
)
async def generate_rent_receipt(
    payload: RentReceiptGenerate,
    db: AsyncSession = Depends(get_db),
    owner_ctx: Owner | None = Depends(get_owner_context),
):
    """
    Crée la quittance (RentReceipt + lignes de détail) à partir des loyers actifs
    du locataire et des frais du mois, comme le cron. Mois courant par défaut.
    Ne génère ni PDF ni email.
    """
    await assert_tenant_scope(db, owner_ctx, payload.tenantId)
    tenant = await db.get(Tenant, payload.tenantId)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if payload.month:
        try:
            year, month = (int(x) for x in payload.month.split("-"))
            date(year, month, 1)
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="month invalide, format attendu YYYY-MM",
            )
    else:
        today = date.today()
        year, month = today.year, today.month

    try:
        receipt, _ = await create_receipt_entry(db, tenant, year, month)
    except ReceiptAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Une quittance existe déjà pour {year}-{month:02d}",
        )
    except NoActiveRentError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Aucun loyer actif pour ce locataire",
        )
    await db.commit()
    await db.refresh(receipt)
    return receipt


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
    force: bool = Query(default=False, description="Régénérer le PDF même s'il existe déjà"),
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
        if force:
            file_path.unlink()
        elif obj.pdfFilename == ctx.filename:
            # Already generated and linked — idempotent, just return
            return {"filename": ctx.filename, "path": f"/files/{ctx.filename}"}
        else:
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


@router.post("/{id}/email", summary="Envoyer le PDF d'une quittance par email")
async def send_receipt_email(
    id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(default=False, description="Envoyer même si sendNoticeOfLeaseRental=0"),
    doc_type: str = Query(description="Type de document : quittance | avis | garantie"),
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

    tenant = await db.get(Tenant, obj.tenantId)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if not force and not tenant.sendNoticeOfLeaseRental:
        return {"sent": False, "reason": "sendNoticeOfLeaseRental=0 (utiliser force=true pour forcer)"}

    tenant_email = tenant.email or ""
    if not tenant_email:
        return {"sent": False, "reason": "pas d'email locataire"}

    ctx = await get_receipt_context(db, id)
    if not ctx.owner_email:
        return {"sent": False, "reason": "pas d'email propriétaire"}

    period_begin = obj.periodBegin
    month_name = MONTHS_FR[period_begin.month - 1] if period_begin else ""
    year = period_begin.year if period_begin else ""
    tenant_name = " ".join(filter(None, [tenant.firstName, tenant.name]))

    if doc_type == "garantie":
        subject = "Reçu de garantie"
        body = f"Bonjour,\n\nVous trouverez ci-joint le reçu du dépot de garantie.\nVous souhaitant bonne réception.\n\nBonne journée,\n{ctx.owner_name}\n"
    elif doc_type == "quittance":
        subject = "Quittance de loyer"
        body = f"Bonjour,\n\nVous trouverez ci-joint la quittance pour le loyer du mois de {month_name} {year}.\nVous souhaitant bonne réception.\n\nBonne journée,\n{ctx.owner_name}\n"
    elif doc_type == "avis":
        subject = "Avis d'échéance"
        body = f"Bonjour,\n\nVous trouverez ci-joint l'avis d'échéance du mois de {month_name} {year}.\nVous souhaitant bonne réception.\n\nBonne journée,\n{ctx.owner_name}\n"
    else:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"doc_type invalide '{doc_type}'. Valeurs acceptées : quittance, avis, garantie")

    unit_obj = await db.get(PlacesUnit, tenant.placeUnitId) if tenant.placeUnitId else None
    if unit_obj and unit_obj.friendlyName:
        subject += f" - {unit_obj.friendlyName}"

    background_tasks.add_task(
        send_pdf_email_sync,
        from_addr=ctx.owner_email,
        from_name=ctx.owner_name,
        to_addr=tenant_email,
        to_name=tenant_name,
        subject=subject,
        body=body,
        pdf_bytes=file_path.read_bytes(),
        pdf_filename=obj.pdfFilename,
        property_name=f"{ctx.unit_zip}-{ctx.place_name}",
    )

    return {"sent": True, "to": tenant_email, "subject": subject}

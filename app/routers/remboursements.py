import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.security import get_current_assureur
from app.models.remboursement import Remboursement
from app.schemas.remboursement import (
    RemboursementCreate,
    RemboursementResponse,
    RemboursementListResponse,
)
from app.services import remboursement_service
from app.services.pdf_service import generer_facture_pdf

router = APIRouter(prefix="/remboursements", tags=["Remboursements"])


@router.get("/assure/{assure_id}", response_model=RemboursementListResponse)
async def get_remboursements_assure(
    assure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """Récupère l'historique des remboursements d'un assuré."""
    items = await remboursement_service.get_remboursements_assure(db, assure_id)
    return RemboursementListResponse(total=len(items), items=items)


@router.post("/", response_model=RemboursementResponse, status_code=201)
async def effectuer_remboursement(
    data: RemboursementCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """
    Effectue un remboursement.
    Calcule automatiquement le taux : 100% généraliste / 80% spécialiste.
    """
    return await remboursement_service.effectuer_remboursement(db, data)


@router.get("/{remboursement_id}/facture")
async def telecharger_facture(
    remboursement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """Génère et télécharge la facture PDF d'un remboursement."""
    result = await db.execute(
        select(Remboursement)
        .options(selectinload(Remboursement.assure))
        .where(Remboursement.id == remboursement_id)
    )
    remboursement = result.scalar_one_or_none()

    if not remboursement:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remboursement introuvable")

    pdf_bytes = generer_facture_pdf(remboursement)

    date_str = remboursement.date_remboursement.strftime("%Y-%m-%d")
    numero = remboursement.assure.numero_assure if remboursement.assure else str(remboursement_id)[:8]
    filename = f"facture-remboursement-{numero}-{date_str}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )

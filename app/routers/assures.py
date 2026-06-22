import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_assureur, get_current_user
from app.schemas.assure import (
    AssureCreate,
    AssureResponse,
    AssureListResponse,
    MedecinTraitantUpdate,
)
from app.services import assure_service

router = APIRouter(prefix="/assures", tags=["Assurés"])


@router.get("", response_model=AssureListResponse)
async def lister_assures(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    recherche: Optional[str] = Query(default=""),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Liste tous les assurés avec pagination et recherche.
    Accessible aux assureurs ET aux médecins (sélection du patient
    lors de la création d'une consultation, d'une feuille de maladie
    ou d'une prescription).
    """
    items, total = await assure_service.lister_assures(db, page, size, recherche)
    return AssureListResponse(total=total, page=page, size=size, items=items)


@router.post("", response_model=AssureResponse, status_code=201)
async def inscrire_assure(
    data: AssureCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """Inscrit un nouvel assuré dans le système."""
    return await assure_service.inscrire_assure(db, data)


@router.get("/{assure_id}", response_model=AssureResponse)
async def get_assure(
    assure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Récupère la fiche complète d'un assuré. Accessible aux assureurs et aux médecins."""
    return await assure_service.get_assure_or_404(db, assure_id)


@router.put("/{assure_id}/medecin-traitant", response_model=AssureResponse)
async def enregistrer_medecin_traitant(
    assure_id: uuid.UUID,
    data: MedecinTraitantUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """Enregistre ou met à jour le médecin traitant d'un assuré (généraliste uniquement)."""
    return await assure_service.enregistrer_medecin_traitant(db, assure_id, data)

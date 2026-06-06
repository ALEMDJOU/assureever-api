import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import get_current_assureur, get_current_medecin, get_current_user
from app.models.feuille_maladie import FeuilleMaladie, StatutFeuilleEnum
from app.schemas.feuille_maladie import (
    FeuilleMaladieCreate,
    FeuilleMaladieComplete,
    FeuilleMaladieResponse,
)

router = APIRouter(prefix="/feuilles-maladie", tags=["Feuilles de Maladie"])


@router.get("/assure/{assure_id}", response_model=list[FeuilleMaladieResponse])
async def get_feuilles_assure(
    assure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Récupère toutes les feuilles de maladie d'un assuré."""
    result = await db.execute(
        select(FeuilleMaladie).where(FeuilleMaladie.assure_id == assure_id)
    )
    return result.scalars().all()


@router.get("/assure/{assure_id}/en-attente", response_model=list[FeuilleMaladieResponse])
async def get_feuilles_en_attente(
    assure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """Récupère les feuilles de maladie complétées et en attente de remboursement."""
    result = await db.execute(
        select(FeuilleMaladie).where(
            FeuilleMaladie.assure_id == assure_id,
            FeuilleMaladie.statut == StatutFeuilleEnum.COMPLETE,
        )
    )
    return result.scalars().all()


@router.post("/", response_model=FeuilleMaladieResponse, status_code=201)
async def enregistrer_feuille(
    data: FeuilleMaladieCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_medecin),
):
    """
    Enregistre une feuille de maladie.
    Acteur : Médecin. Vérifie l'absence de doublon (même consultation).
    """
    # Contrôle doublon sur la consultation
    existing = await db.execute(
        select(FeuilleMaladie).where(FeuilleMaladie.consultation_id == data.consultation_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Une feuille de maladie existe déjà pour cette consultation",
        )

    feuille = FeuilleMaladie(
        assure_id=data.assure_id,
        consultation_id=data.consultation_id,
        montant_consultation=data.montant_consultation,
        observations=data.observations,
        statut=StatutFeuilleEnum.EN_ATTENTE,
    )
    db.add(feuille)
    await db.flush()
    await db.refresh(feuille)
    return feuille


@router.patch("/{feuille_id}", response_model=FeuilleMaladieResponse)
async def completer_feuille(
    feuille_id: uuid.UUID,
    data: FeuilleMaladieComplete,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """
    Complète une feuille de maladie (ajoute les mentions de l'assureur).
    Passe le statut de EN_ATTENTE à COMPLETE.
    """
    result = await db.execute(select(FeuilleMaladie).where(FeuilleMaladie.id == feuille_id))
    feuille = result.scalar_one_or_none()

    if not feuille:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feuille introuvable")

    if feuille.statut != StatutFeuilleEnum.EN_ATTENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les feuilles EN_ATTENTE peuvent être complétées",
        )

    if data.observations is not None:
        feuille.observations = data.observations
    if data.montant_consultation is not None:
        feuille.montant_consultation = data.montant_consultation

    feuille.statut = StatutFeuilleEnum.COMPLETE
    await db.flush()
    await db.refresh(feuille)
    return feuille

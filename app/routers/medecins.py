import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.core.security import get_current_assureur, get_current_user
from app.models.medecin import Medecin, TypeMedecinEnum
from app.schemas.medecin import MedecinCreate, MedecinResponse, MedecinListResponse

router = APIRouter(prefix="/medecins", tags=["Médecins"])


@router.get("/", response_model=MedecinListResponse)
async def lister_medecins(
    type_medecin: Optional[TypeMedecinEnum] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Liste tous les médecins, avec filtre optionnel par type."""
    stmt = select(Medecin)
    if type_medecin:
        stmt = stmt.where(Medecin.type_medecin == type_medecin)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return MedecinListResponse(total=len(items), items=items)


@router.post("/", response_model=MedecinResponse, status_code=201)
async def enregistrer_medecin(
    data: MedecinCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """Enregistre un nouveau médecin dans le système."""
    medecin = Medecin(
        matricule=data.matricule,
        nom=data.nom,
        prenom=data.prenom,
        type_medecin=data.type_medecin,
        specialite=data.specialite,
        telephone=data.telephone,
    )
    db.add(medecin)
    await db.flush()
    await db.refresh(medecin)
    return medecin


@router.get("/{medecin_id}", response_model=MedecinResponse)
async def get_medecin(
    medecin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Récupère la fiche d'un médecin."""
    result = await db.execute(select(Medecin).where(Medecin.id == medecin_id))
    medecin = result.scalar_one_or_none()
    if not medecin:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Médecin introuvable")
    return medecin

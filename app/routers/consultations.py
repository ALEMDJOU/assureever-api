import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import get_current_medecin, get_current_user
from app.models.consultation import Consultation
from app.models.medecin import Medecin
from app.models.assure import Assure
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationListResponse,
)

router = APIRouter(prefix="/consultations", tags=["Consultations"])


async def _get_medecin_by_user_id(db: AsyncSession, user_id: str) -> Medecin:
    result = await db.execute(
        select(Medecin).where(Medecin.user_id == uuid.UUID(user_id))
    )
    medecin = result.scalar_one_or_none()
    if not medecin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiche médecin introuvable pour ce compte",
        )
    return medecin


@router.post("/", response_model=ConsultationResponse, status_code=201)
async def creer_consultation(
    data: ConsultationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_medecin),
):
    """
    Enregistre une nouvelle consultation.
    UC6 — Acteur : Médecin uniquement.
    """
    medecin = await _get_medecin_by_user_id(db, current_user["id"])

    # Vérifier que l'assuré existe
    assure_result = await db.execute(select(Assure).where(Assure.id == data.assure_id))
    if not assure_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assuré introuvable",
        )

    consultation = Consultation(
        assure_id=data.assure_id,
        medecin_id=medecin.id,
        date_consultation=data.date_consultation,
        motif=data.motif,
        diagnostic=data.diagnostic,
        actes_realises=data.actes_realises,
        montant_consultation=data.montant_consultation,
    )
    db.add(consultation)
    await db.flush()
    await db.refresh(consultation)
    return consultation


@router.get("/mes-consultations", response_model=ConsultationListResponse)
async def mes_consultations(
    assure_id: uuid.UUID = Query(default=None, description="Filtrer par assuré"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_medecin),
):
    """
    Liste les consultations du médecin connecté.
    Filtre optionnel par assuré.
    """
    medecin = await _get_medecin_by_user_id(db, current_user["id"])

    stmt = select(Consultation).where(Consultation.medecin_id == medecin.id)
    if assure_id:
        stmt = stmt.where(Consultation.assure_id == assure_id)
    stmt = stmt.order_by(Consultation.date_consultation.desc())

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return ConsultationListResponse(total=len(items), items=items)


@router.get("/assure/{assure_id}", response_model=ConsultationListResponse)
async def consultations_assure(
    assure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Liste toutes les consultations d'un assuré.
    Accessible aux médecins et aux assureurs.
    """
    stmt = (
        select(Consultation)
        .where(Consultation.assure_id == assure_id)
        .order_by(Consultation.date_consultation.desc())
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return ConsultationListResponse(total=len(items), items=items)


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Récupère le détail d'une consultation."""
    result = await db.execute(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    consultation = result.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation introuvable")
    return consultation

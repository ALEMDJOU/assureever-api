import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_assureur, get_current_user
from app.models.medecin import TypeMedecinEnum
from app.schemas.medecin import (
    MedecinCreate,
    MedecinUpdate,
    MedecinResponse,
    MedecinListResponse,
)
from app.services import medecin_service

router = APIRouter(prefix="/medecins", tags=["Médecins"])


@router.get("/", response_model=MedecinListResponse)
async def lister_medecins(
    type_medecin: Optional[TypeMedecinEnum] = Query(
        default=None,
        description="Filtrer par type : GENERALISTE ou SPECIALISTE"
    ),
    recherche: Optional[str] = Query(
        default="",
        description="Recherche par nom, prénom, matricule ou spécialité"
    ),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Liste tous les médecins enregistrés dans le système.
    Accessible aux assureurs et aux médecins (ex : trouver un spécialiste — UC8).
    Filtre par type et/ou recherche textuelle.
    """
    items, total = await medecin_service.lister_medecins(db, type_medecin, recherche)
    return MedecinListResponse(total=total, items=items)


@router.post("/", response_model=MedecinResponse, status_code=201)
async def enregistrer_medecin(
    data: MedecinCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """
    Enregistre un nouveau médecin dans le système.

    **UC0 — Acteur : Assureur uniquement.**

    Ce cas d'utilisation est absent du cahier d'analyse original (lacune identifiée).
    Il est cependant indispensable car :
    - UC2 requiert que le médecin traitant existe dans le système.
    - UC8 pose comme pré-condition que le spécialiste existe dans le système.
    - Le package «Inscriptions» décrit explicitement l'enregistrement des médecins.

    **Règles métier :**
    - Contrôle de doublon sur le matricule (identifiant professionnel).
    - Contrôle de doublon sur l'email (compte utilisateur).
    - Si type = SPECIALISTE → le champ `specialite` est obligatoire.
    - Si type = GENERALISTE → le champ `specialite` est ignoré.
    - Un compte utilisateur (rôle MEDECIN) est créé simultanément
      pour permettre au médecin de s'authentifier.
    """
    return await medecin_service.enregistrer_medecin(db, data)


@router.get("/generalistes", response_model=MedecinListResponse)
async def lister_generalistes(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """
    Liste uniquement les médecins généralistes.
    Utilisé lors de l'association d'un médecin traitant à un assuré (UC2).
    """
    items, total = await medecin_service.lister_medecins(db, TypeMedecinEnum.GENERALISTE)
    return MedecinListResponse(total=total, items=items)


@router.get("/specialistes", response_model=MedecinListResponse)
async def lister_specialistes(
    specialite: Optional[str] = Query(
        default=None,
        description="Filtrer par spécialité (ex: Cardiologie, Ophtalmologie)"
    ),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Liste uniquement les médecins spécialistes.
    Utilisé lors d'une prescription de consultation spécialisée (UC8).
    Filtre optionnel par spécialité.
    """
    items, total = await medecin_service.lister_medecins(
        db, TypeMedecinEnum.SPECIALISTE, specialite or ""
    )
    return MedecinListResponse(total=total, items=items)


@router.get("/{medecin_id}", response_model=MedecinResponse)
async def get_medecin(
    medecin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Récupère la fiche complète d'un médecin."""
    return await medecin_service.get_medecin_or_404(db, medecin_id)


@router.patch("/{medecin_id}", response_model=MedecinResponse)
async def mettre_a_jour_medecin(
    medecin_id: uuid.UUID,
    data: MedecinUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """
    Met à jour partiellement la fiche d'un médecin.
    Acteur : Assureur uniquement. Seuls le téléphone et la spécialité sont modifiables.
    """
    return await medecin_service.mettre_a_jour_medecin(db, medecin_id, data)


@router.delete("/{medecin_id}", status_code=200)
async def desactiver_medecin(
    medecin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_assureur),
):
    """
    Désactive le compte utilisateur d'un médecin.
    Les données (consultations, feuilles, prescriptions) sont conservées.
    Acteur : Assureur uniquement.
    """
    return await medecin_service.desactiver_medecin(db, medecin_id)

import uuid
import random
import string
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.assure import Assure
from app.models.medecin import Medecin, TypeMedecinEnum
from app.schemas.assure import AssureCreate, AssureUpdate, MedecinTraitantUpdate


def _generer_numero_assure() -> str:
    """Génère un numéro d'assuré unique au format SS-XXXXXXXX."""
    suffixe = "".join(random.choices(string.digits, k=8))
    return f"SS-{suffixe}"


async def inscrire_assure(db: AsyncSession, data: AssureCreate) -> Assure:
    """
    Inscrit un nouvel assuré.
    Vérifie l'absence de doublon (même nom + prénom + date_naissance).
    Conforme au scénario UC1 du cahier d'analyse.
    """
    # Contrôle de doublon
    stmt = select(Assure).where(
        Assure.nom.ilike(data.nom),
        Assure.prenom.ilike(data.prenom),
        Assure.date_naissance == data.date_naissance,
    )
    result = await db.execute(stmt)
    existant = result.scalar_one_or_none()

    if existant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un assuré avec ces informations existe déjà (N° {existant.numero_assure})",
        )

    # Génération du numéro unique (avec retry si collision)
    for _ in range(5):
        numero = _generer_numero_assure()
        check = await db.execute(select(Assure).where(Assure.numero_assure == numero))
        if not check.scalar_one_or_none():
            break

    assure = Assure(
        numero_assure=numero,
        nom=data.nom.strip(),
        prenom=data.prenom.strip(),
        date_naissance=data.date_naissance,
        adresse=data.adresse,
        telephone=data.telephone,
        email=data.email,
    )
    db.add(assure)
    await db.flush()
    await db.refresh(assure)
    return assure


async def get_assure_or_404(db: AsyncSession, assure_id: uuid.UUID) -> Assure:
    result = await db.execute(select(Assure).where(Assure.id == assure_id))
    assure = result.scalar_one_or_none()
    if not assure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assuré introuvable",
        )
    return assure


async def lister_assures(
    db: AsyncSession, page: int = 1, size: int = 20, recherche: str = ""
) -> tuple[list[Assure], int]:
    offset = (page - 1) * size
    stmt = select(Assure)
    if recherche:
        stmt = stmt.where(
            or_(
                Assure.nom.ilike(f"%{recherche}%"),
                Assure.prenom.ilike(f"%{recherche}%"),
                Assure.numero_assure.ilike(f"%{recherche}%"),
            )
        )
    count_result = await db.execute(stmt)
    total = len(count_result.scalars().all())

    stmt = stmt.offset(offset).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def enregistrer_medecin_traitant(
    db: AsyncSession, assure_id: uuid.UUID, data: MedecinTraitantUpdate
) -> Assure:
    """
    Associe un médecin traitant à un assuré.
    Règle métier : le médecin doit être un GENERALISTE (UC2 du cahier).
    """
    assure = await get_assure_or_404(db, assure_id)

    result = await db.execute(select(Medecin).where(Medecin.id == data.medecin_id))
    medecin = result.scalar_one_or_none()

    if not medecin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médecin introuvable",
        )

    # Règle métier : seul un généraliste peut être médecin traitant
    if medecin.type_medecin != TypeMedecinEnum.GENERALISTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seul un médecin généraliste peut être désigné comme médecin traitant",
        )

    assure.medecin_traitant_id = medecin.id
    await db.flush()
    await db.refresh(assure)
    return assure

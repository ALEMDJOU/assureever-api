"""
Service d'enregistrement des médecins.

UC0 — Enregistrer un médecin (Acteur : Assureur)
Ce cas d'utilisation est absent du cahier d'analyse (lacune identifiée),
mais indispensable : UC8 pose comme pré-condition que "le spécialiste existe
dans le système", et le package Inscriptions décrit explicitement
"l'enregistrement des médecins au sein de l'organisme de sécurité sociale".

Règles métier implémentées :
  1. Contrôle de doublon sur le matricule (identifiant professionnel unique).
  2. Contrôle de doublon sur l'email (compte utilisateur unique).
  3. Si type_medecin == SPECIALISTE, le champ `specialite` est obligatoire.
  4. Si type_medecin == GENERALISTE, le champ `specialite` est ignoré
     (un généraliste n'a pas de spécialité au sens médical).
  5. Création atomique : fiche Medecin + compte User dans la même transaction.
     Si l'une échoue, l'autre est annulée.
"""

import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.medecin import Medecin, TypeMedecinEnum
from app.models.user import User, RoleEnum
from app.schemas.medecin import MedecinCreate, MedecinUpdate
from app.core.hashing import hash_password



async def enregistrer_medecin(db: AsyncSession, data: MedecinCreate) -> Medecin:
    """
    Enregistre un nouveau médecin et crée son compte utilisateur.

    Pré-conditions :
      - Le matricule n'existe pas encore dans le système.
      - L'email n'est pas déjà utilisé.
      - Si SPECIALISTE, la spécialité est renseignée.

    Post-conditions :
      - Une fiche Medecin est créée.
      - Un compte User (rôle MEDECIN) est créé et lié à la fiche.
      - Le médecin peut s'authentifier immédiatement.
    """

    # 1. Contrôle de doublon sur le matricule
    existing_matricule = await db.execute(
        select(Medecin).where(Medecin.matricule == data.matricule.strip())
    )
    if existing_matricule.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un médecin avec le matricule «{data.matricule}» existe déjà dans le système",
        )

    # 2. Contrôle de doublon sur l'email
    existing_email = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette adresse email est déjà associée à un compte",
        )

    # 3. Règle métier : spécialité obligatoire pour un spécialiste
    if data.type_medecin == TypeMedecinEnum.SPECIALISTE and not data.specialite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le champ 'specialite' est obligatoire pour un médecin spécialiste",
        )

    # 4. Règle métier : un généraliste n'a pas de spécialité
    specialite = None
    if data.type_medecin == TypeMedecinEnum.SPECIALISTE:
        specialite = data.specialite.strip() if data.specialite else None

    # 5. Création du compte utilisateur (pour l'authentification)
    user = User(
        nom=data.nom.strip(),
        prenom=data.prenom.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role=RoleEnum.MEDECIN,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # Obtenir user.id sans committer

    # 6. Création de la fiche médecin liée au compte
    medecin = Medecin(
        matricule=data.matricule.strip(),
        nom=data.nom.strip(),
        prenom=data.prenom.strip(),
        type_medecin=data.type_medecin,
        specialite=specialite,
        telephone=data.telephone,
        user_id=user.id,
    )
    db.add(medecin)
    await db.flush()
    await db.refresh(medecin)

    # Enrichir la réponse avec l'email depuis le User
    medecin.email = user.email  # Attribut temporaire pour la sérialisation
    return medecin


async def get_medecin_or_404(db: AsyncSession, medecin_id: uuid.UUID) -> Medecin:
    result = await db.execute(select(Medecin).where(Medecin.id == medecin_id))
    medecin = result.scalar_one_or_none()
    if not medecin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médecin introuvable",
        )
    await _enrichir_email(db, medecin)
    return medecin


async def lister_medecins(
    db: AsyncSession,
    type_medecin: TypeMedecinEnum | None = None,
    recherche: str = "",
) -> tuple[list[Medecin], int]:
    """
    Liste les médecins avec filtre optionnel par type et recherche textuelle.
    Utilisé notamment par le médecin pour trouver un spécialiste (UC8).
    """
    from sqlalchemy import or_
    stmt = select(Medecin)

    if type_medecin:
        stmt = stmt.where(Medecin.type_medecin == type_medecin)

    if recherche:
        stmt = stmt.where(
            or_(
                Medecin.nom.ilike(f"%{recherche}%"),
                Medecin.prenom.ilike(f"%{recherche}%"),
                Medecin.matricule.ilike(f"%{recherche}%"),
                Medecin.specialite.ilike(f"%{recherche}%"),
            )
        )

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    for medecin in items:
        await _enrichir_email(db, medecin)
    return items, len(items)


async def _enrichir_email(db: AsyncSession, medecin: Medecin) -> None:
    """Renseigne l'attribut transitoire `email` depuis le User lié, pour la sérialisation."""
    if not medecin.user_id:
        medecin.email = None
        return
    result = await db.execute(select(User).where(User.id == medecin.user_id))
    user = result.scalar_one_or_none()
    medecin.email = user.email if user else None


async def mettre_a_jour_medecin(
    db: AsyncSession,
    medecin_id: uuid.UUID,
    data: MedecinUpdate,
) -> Medecin:
    """Mise à jour partielle d'une fiche médecin (téléphone, spécialité)."""
    medecin = await get_medecin_or_404(db, medecin_id)

    if data.telephone is not None:
        medecin.telephone = data.telephone

    if data.specialite is not None:
        if medecin.type_medecin == TypeMedecinEnum.GENERALISTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un médecin généraliste ne peut pas avoir de spécialité",
            )
        medecin.specialite = data.specialite.strip()

    await db.flush()
    await db.refresh(medecin)
    return medecin


async def desactiver_medecin(db: AsyncSession, medecin_id: uuid.UUID) -> dict:
    """
    Désactive le compte utilisateur d'un médecin sans supprimer ses données.
    Préserve l'historique des consultations, feuilles et prescriptions.
    """
    medecin = await get_medecin_or_404(db, medecin_id)

    if medecin.user_id:
        result = await db.execute(select(User).where(User.id == medecin.user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = False
            await db.flush()

    return {"message": f"Compte du Dr. {medecin.nom} {medecin.prenom} désactivé"}

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.remboursement import Remboursement, StatutRemboursementEnum
from app.models.feuille_maladie import FeuilleMaladie, StatutFeuilleEnum
from app.models.medecin import TypeMedecinEnum
from app.models.consultation import Consultation
from app.schemas.remboursement import RemboursementCreate

# Taux de remboursement selon le type de médecin (règle métier du cahier)
TAUX_GENERALISTE = 100.0
TAUX_SPECIALISTE = 80.0


async def effectuer_remboursement(
    db: AsyncSession, data: RemboursementCreate
) -> Remboursement:
    """
    Effectue un remboursement pour une feuille de maladie.
    - Calcule automatiquement le taux (100% généraliste / 80% spécialiste)
    - Met à jour le statut de la feuille de maladie
    Conforme au UC3 du cahier d'analyse.
    """
    # Charger la feuille de maladie avec sa consultation et son médecin
    stmt = (
        select(FeuilleMaladie)
        .where(FeuilleMaladie.id == data.feuille_maladie_id)
        .options(
            selectinload(FeuilleMaladie.consultation).selectinload(Consultation.medecin)
        )
    )
    result = await db.execute(stmt)
    feuille = result.scalar_one_or_none()

    if not feuille:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feuille de maladie introuvable",
        )

    if feuille.assure_id != data.assure_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette feuille de maladie n'appartient pas à cet assuré",
        )

    if feuille.statut == StatutFeuilleEnum.REMBOURSEE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette feuille de maladie a déjà été remboursée",
        )

    if feuille.statut != StatutFeuilleEnum.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La feuille de maladie doit être complétée avant d'être remboursée",
        )

    # Calcul automatique du taux selon le type de médecin
    medecin = feuille.consultation.medecin
    if medecin.type_medecin == TypeMedecinEnum.GENERALISTE:
        taux = TAUX_GENERALISTE
    else:
        taux = TAUX_SPECIALISTE

    montant_consultation = feuille.montant_consultation
    montant_rembourse = round(montant_consultation * taux / 100, 2)

    remboursement = Remboursement(
        assure_id=data.assure_id,
        feuille_maladie_id=data.feuille_maladie_id,
        taux_remboursement=taux,
        montant_consultation=montant_consultation,
        montant_rembourse=montant_rembourse,
        mode_paiement=data.mode_paiement,
        reference_virement=data.reference_virement,
        statut=StatutRemboursementEnum.PAYE,
    )

    # Mise à jour du statut de la feuille
    feuille.statut = StatutFeuilleEnum.REMBOURSEE

    db.add(remboursement)
    await db.flush()
    await db.refresh(remboursement)
    return remboursement


async def get_remboursements_assure(
    db: AsyncSession, assure_id: uuid.UUID
) -> list[Remboursement]:
    stmt = select(Remboursement).where(Remboursement.assure_id == assure_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_tous_remboursements(db: AsyncSession) -> list[Remboursement]:
    stmt = select(Remboursement)
    result = await db.execute(stmt)
    return result.scalars().all()


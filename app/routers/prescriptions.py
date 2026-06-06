import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import get_current_medecin
from app.models.prescription import (
    Prescription, PrescriptionMedicament, PrescriptionConsultation, TypePrescriptionEnum
)
from app.models.medecin import Medecin, TypeMedecinEnum
from app.schemas.prescription import (
    PrescriptionMedicamentCreate,
    PrescriptionConsultationCreate,
    PrescriptionMedicamentResponse,
    PrescriptionConsultationResponse,
)

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


@router.post("/medicament", response_model=PrescriptionMedicamentResponse, status_code=201)
async def prescrire_medicament(
    data: PrescriptionMedicamentCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_medecin),
):
    """Prescrit un médicament pour une consultation. Acteur : Médecin."""
    prescription = Prescription(
        consultation_id=data.consultation_id,
        type_prescription=TypePrescriptionEnum.MEDICAMENT,
    )
    db.add(prescription)
    await db.flush()

    presc_med = PrescriptionMedicament(
        prescription_id=prescription.id,
        nom_medicament=data.nom_medicament,
        dosage=data.dosage,
        posologie=data.posologie,
        duree_traitement_jours=data.duree_traitement_jours,
    )
    db.add(presc_med)
    await db.flush()
    await db.refresh(presc_med)

    return PrescriptionMedicamentResponse(
        id=presc_med.id,
        nom_medicament=presc_med.nom_medicament,
        dosage=presc_med.dosage,
        posologie=presc_med.posologie,
        duree_traitement_jours=presc_med.duree_traitement_jours,
        date_prescription=prescription.date_prescription,
    )


@router.post("/consultation-specialiste", response_model=PrescriptionConsultationResponse, status_code=201)
async def prescrire_consultation_specialiste(
    data: PrescriptionConsultationCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_medecin),
):
    """
    Prescrit une consultation chez un spécialiste.
    Vérifie que le médecin cible est bien un SPECIALISTE.
    """
    if data.specialiste_id:
        result = await db.execute(select(Medecin).where(Medecin.id == data.specialiste_id))
        specialiste = result.scalar_one_or_none()

        if not specialiste:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médecin spécialiste introuvable",
            )
        if specialiste.type_medecin != TypeMedecinEnum.SPECIALISTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le médecin sélectionné n'est pas un spécialiste",
            )

    prescription = Prescription(
        consultation_id=data.consultation_id,
        type_prescription=TypePrescriptionEnum.CONSULTATION_SPECIALISTE,
    )
    db.add(prescription)
    await db.flush()

    presc_consult = PrescriptionConsultation(
        prescription_id=prescription.id,
        motif=data.motif,
        specialiste_id=data.specialiste_id,
    )
    db.add(presc_consult)
    await db.flush()
    await db.refresh(presc_consult)

    return PrescriptionConsultationResponse(
        id=presc_consult.id,
        motif=presc_consult.motif,
        specialiste_id=presc_consult.specialiste_id,
        date_prescription=prescription.date_prescription,
    )

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PrescriptionMedicamentCreate(BaseModel):
    consultation_id: uuid.UUID
    nom_medicament: str
    dosage: str
    posologie: str
    duree_traitement_jours: int


class PrescriptionConsultationCreate(BaseModel):
    consultation_id: uuid.UUID
    motif: str
    specialiste_id: Optional[uuid.UUID] = None


class PrescriptionMedicamentResponse(BaseModel):
    id: uuid.UUID
    nom_medicament: str
    dosage: str
    posologie: str
    duree_traitement_jours: int
    date_prescription: datetime

    model_config = {"from_attributes": True}


class PrescriptionConsultationResponse(BaseModel):
    id: uuid.UUID
    motif: str
    specialiste_id: Optional[uuid.UUID]
    date_prescription: datetime

    model_config = {"from_attributes": True}

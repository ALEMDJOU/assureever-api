import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.models.feuille_maladie import StatutFeuilleEnum


class FeuilleMaladieCreate(BaseModel):
    assure_id: uuid.UUID
    consultation_id: uuid.UUID
    montant_consultation: float
    observations: Optional[str] = None


class FeuilleMaladieComplete(BaseModel):
    observations: Optional[str] = None
    montant_consultation: Optional[float] = None


class FeuilleMaladieResponse(BaseModel):
    id: uuid.UUID
    assure_id: uuid.UUID
    consultation_id: uuid.UUID
    statut: StatutFeuilleEnum
    montant_consultation: float
    observations: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

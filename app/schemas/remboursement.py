import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.models.remboursement import ModePaiementEnum, StatutRemboursementEnum


class RemboursementCreate(BaseModel):
    assure_id: uuid.UUID
    feuille_maladie_id: uuid.UUID
    mode_paiement: ModePaiementEnum
    reference_virement: Optional[str] = None


class RemboursementResponse(BaseModel):
    id: uuid.UUID
    assure_id: uuid.UUID
    feuille_maladie_id: uuid.UUID
    taux_remboursement: float
    montant_consultation: float
    montant_rembourse: float
    mode_paiement: ModePaiementEnum
    statut: StatutRemboursementEnum
    reference_virement: Optional[str]
    date_remboursement: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class RemboursementListResponse(BaseModel):
    total: int
    items: list[RemboursementResponse]

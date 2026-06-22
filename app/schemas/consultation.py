import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ConsultationCreate(BaseModel):
    assure_id: uuid.UUID
    date_consultation: date
    motif: str
    diagnostic: Optional[str] = None
    actes_realises: Optional[str] = None
    montant_consultation: float

    @field_validator("motif")
    @classmethod
    def motif_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Le motif ne peut pas être vide")
        return v.strip()

    @field_validator("montant_consultation")
    @classmethod
    def montant_positif(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Le montant doit être positif")
        return v


class ConsultationResponse(BaseModel):
    id: uuid.UUID
    assure_id: uuid.UUID
    medecin_id: uuid.UUID
    date_consultation: date
    motif: str
    diagnostic: Optional[str]
    actes_realises: Optional[str]
    montant_consultation: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsultationListResponse(BaseModel):
    total: int
    items: list[ConsultationResponse]

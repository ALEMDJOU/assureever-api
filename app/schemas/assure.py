import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class AssureCreate(BaseModel):
    nom: str
    prenom: str
    date_naissance: date
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("nom", "prenom")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ce champ ne peut pas être vide")
        return v.strip()


class AssureUpdate(BaseModel):
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None


class MedecinTraitantUpdate(BaseModel):
    medecin_id: uuid.UUID


class AssureResponse(BaseModel):
    id: uuid.UUID
    numero_assure: str
    nom: str
    prenom: str
    date_naissance: date
    adresse: Optional[str]
    telephone: Optional[str]
    email: Optional[str]
    medecin_traitant_id: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


class AssureListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[AssureResponse]

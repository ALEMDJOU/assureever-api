import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.models.medecin import TypeMedecinEnum


class MedecinCreate(BaseModel):
    matricule: str
    nom: str
    prenom: str
    type_medecin: TypeMedecinEnum
    specialite: Optional[str] = None
    telephone: Optional[str] = None


class MedecinResponse(BaseModel):
    id: uuid.UUID
    matricule: str
    nom: str
    prenom: str
    type_medecin: TypeMedecinEnum
    specialite: Optional[str]
    telephone: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class MedecinListResponse(BaseModel):
    total: int
    items: list[MedecinResponse]

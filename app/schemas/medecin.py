import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator
from app.models.medecin import TypeMedecinEnum


class MedecinCreate(BaseModel):
    """
    Schéma d'enregistrement d'un médecin.
    UC0 (non modélisé dans le cahier) — Acteur : Assureur.
    Crée simultanément la fiche médecin ET un compte utilisateur
    pour permettre au médecin de s'authentifier dans le système.
    """
    # Informations professionnelles
    matricule: str
    nom: str
    prenom: str
    type_medecin: TypeMedecinEnum
    # Obligatoire si type_medecin == SPECIALISTE
    specialite: Optional[str] = None
    telephone: Optional[str] = None

    # Compte utilisateur (pour l'authentification du médecin)
    email: EmailStr
    password: str

    @field_validator("matricule", "nom", "prenom")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ce champ ne peut pas être vide")
        return v.strip()

    @field_validator("specialite")
    @classmethod
    def specialite_requise_si_specialiste(cls, v, info):
        # La validation croisée type_medecin/specialite est gérée dans le service
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v


class MedecinUpdate(BaseModel):
    """Mise à jour partielle d'une fiche médecin."""
    telephone: Optional[str] = None
    specialite: Optional[str] = None


class MedecinResponse(BaseModel):
    id: uuid.UUID
    matricule: str
    nom: str
    prenom: str
    type_medecin: TypeMedecinEnum
    specialite: Optional[str]
    telephone: Optional[str]
    email: Optional[str] = None   # Exposé depuis le User lié
    created_at: datetime

    model_config = {"from_attributes": True}


class MedecinListResponse(BaseModel):
    total: int
    items: list[MedecinResponse]

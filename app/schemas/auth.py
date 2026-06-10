from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterAssureurRequest(BaseModel):
    """
    Inscription d'un agent assureur.
    Seul le rôle ASSUREUR est autorisé via cet endpoint public.
    Les médecins sont créés par les assureurs (UC0) via /medecins.
    """
    nom: str
    prenom: str
    email: EmailStr
    password: str

    @field_validator("nom", "prenom")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ce champ ne peut pas être vide")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: str
    nom: str
    prenom: str
    email: str
    role: RoleEnum


TokenResponse.model_rebuild()

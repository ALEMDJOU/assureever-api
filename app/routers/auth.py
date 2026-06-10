from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterAssureurRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login/medecin", response_model=TokenResponse)
async def login_medecin(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Connexion réservée aux médecins.
    Retourne 403 si les identifiants correspondent à un compte assureur.
    """
    return await auth_service.login_medecin(db, data)


@router.post("/login/assureur", response_model=TokenResponse)
async def login_assureur(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Connexion réservée à l'assureur unique.
    Retourne 403 si les identifiants correspondent à un compte médecin.
    """
    return await auth_service.login_assureur(db, data)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterAssureurRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Inscrit l'assureur unique du système.
    Endpoint public — refusé (409) si un assureur existe déjà.
    Les médecins sont créés par l'assureur via POST /api/v1/medecins.
    """
    return await auth_service.register_assureur(db, data)

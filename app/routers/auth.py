from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterAssureurRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authentifie un utilisateur (assureur ou médecin).
    Retourne un JWT signé compatible avec NextAuth.js v5.
    Le token contient : sub (user_id), email, role, nom, prenom.
    """
    return await auth_service.login(db, data)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterAssureurRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Inscrit un nouvel agent assureur.
    **Endpoint public** — aucun token requis.
    Seul le rôle ASSUREUR est autorisé via cet endpoint.
    Les médecins sont créés par les assureurs via POST /api/v1/medecins.
    """
    return await auth_service.register_assureur(db, data)


@router.get("/me", response_model=dict)
async def me(db: AsyncSession = Depends(get_db)):
    """Endpoint de test — retourne le statut de l'API auth."""
    return {"statut": "auth service opérationnel"}

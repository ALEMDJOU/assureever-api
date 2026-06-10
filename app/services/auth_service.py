"""
Service d'authentification.

- login       : vérifie email + mot de passe, retourne un JWT signé.
- register    : inscrit un nouvel agent assureur (endpoint public).

Le JWT émis est signé avec NEXTAUTH_SECRET afin d'être
vérifiable par le middleware FastAPI ET par NextAuth.js v5.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, RoleEnum
from app.schemas.auth import LoginRequest, RegisterAssureurRequest, TokenResponse, UserInfo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def _create_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub":   str(user.id),
        "email": user.email,
        "role":  user.role.value,
        "nom":   user.nom,
        "prenom": user.prenom,
        "exp":   expire,
        "iat":   datetime.utcnow(),
    }
    return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm=ALGORITHM)


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    # Chercher l'utilisateur par email
    result = await db.execute(
        select(User).where(User.email == data.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé. Contactez l'administrateur.",
        )

    token = _create_token(user)

    return TokenResponse(
        access_token=token,
        user=UserInfo(
            id=str(user.id),
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            role=user.role,
        ),
    )


async def register_assureur(
    db: AsyncSession, data: RegisterAssureurRequest
) -> TokenResponse:
    """
    Inscrit un nouvel agent assureur.
    Endpoint public — seul ASSUREUR est autorisé ici.
    Les médecins sont créés par les assureurs via POST /medecins.
    """
    # Contrôle de doublon email
    existing = await db.execute(
        select(User).where(User.email == data.email.lower().strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    user = User(
        nom=data.nom.strip(),
        prenom=data.prenom.strip(),
        email=data.email.lower().strip(),
        password_hash=pwd_context.hash(data.password),
        role=RoleEnum.ASSUREUR,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = _create_token(user)

    return TokenResponse(
        access_token=token,
        user=UserInfo(
            id=str(user.id),
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            role=user.role,
        ),
    )

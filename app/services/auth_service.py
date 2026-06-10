"""
Service d'authentification.

- login              : vérifie email + mot de passe, retourne un JWT signé.
- register_assureur  : inscrit l'assureur unique du système (endpoint public,
                       mais refusé si un assureur existe déjà).

Le JWT émis est signé avec NEXTAUTH_SECRET afin d'être
vérifiable par le middleware FastAPI ET par NextAuth.js v5.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.hashing import hash_password, verify_password
from app.models.user import User, RoleEnum
from app.schemas.auth import LoginRequest, RegisterAssureurRequest, TokenResponse, UserInfo


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def _create_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub":    str(user.id),
        "email":  user.email,
        "role":   user.role.value,
        "nom":    user.nom,
        "prenom": user.prenom,
        "exp":    expire,
        "iat":    datetime.utcnow(),
    }
    return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm=ALGORITHM)


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == data.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé. Contactez l'administrateur.",
        )

    return TokenResponse(
        access_token=_create_token(user),
        user=UserInfo(
            id=str(user.id),
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            role=user.role,
        ),
    )


async def login_medecin(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """
    Connexion réservée aux médecins.
    Refuse explicitement si le compte trouvé est un ASSUREUR.
    """
    result = await db.execute(
        select(User).where(User.email == data.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if user.role != RoleEnum.MEDECIN:
        # Ne pas révéler l'existence d'un compte assureur
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cet espace est réservé aux médecins. Les agents assureurs utilisent l'espace dédié.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé. Contactez l'assureur.",
        )

    return TokenResponse(
        access_token=_create_token(user),
        user=UserInfo(
            id=str(user.id),
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            role=user.role,
        ),
    )


async def login_assureur(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """
    Connexion réservée à l'assureur unique.
    Refuse explicitement si le compte trouvé est un MEDECIN.
    """
    result = await db.execute(
        select(User).where(User.email == data.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if user.role != RoleEnum.ASSUREUR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cet espace est réservé à l'agent assureur.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    return TokenResponse(
        access_token=_create_token(user),
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
    Inscrit l'assureur unique du système.
    Endpoint public — refusé si un assureur existe déjà en base.
    """
    # Règle de sécurité : un seul assureur autorisé dans le système
    existing_assureur = await db.execute(
        select(User).where(User.role == RoleEnum.ASSUREUR)
    )
    if existing_assureur.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte assureur existe déjà. Ce système n'autorise qu'un seul assureur.",
        )

    # Contrôle doublon email
    existing_email = await db.execute(
        select(User).where(User.email == data.email.lower().strip())
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    user = User(
        nom=data.nom.strip(),
        prenom=data.prenom.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role=RoleEnum.ASSUREUR,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return TokenResponse(
        access_token=_create_token(user),
        user=UserInfo(
            id=str(user.id),
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            role=user.role,
        ),
    )

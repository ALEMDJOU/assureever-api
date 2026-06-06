from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_db
from app.models.user import RoleEnum

bearer_scheme = HTTPBearer()

ALGORITHM = "HS256"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Vérifie le JWT émis par NextAuth.js et retourne l'utilisateur courant.
    Le secret doit être identique à NEXTAUTH_SECRET côté Next.js.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.NEXTAUTH_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None or role is None:
            raise credentials_exception

        return {"id": user_id, "role": role}

    except JWTError:
        raise credentials_exception


async def get_current_assureur(
    current_user: dict = Depends(get_current_user),
):
    """Dépendance réservée aux agents assureurs."""
    if current_user.get("role") != RoleEnum.ASSUREUR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux agents assureurs",
        )
    return current_user


async def get_current_medecin(
    current_user: dict = Depends(get_current_user),
):
    """Dépendance réservée aux médecins."""
    if current_user.get("role") != RoleEnum.MEDECIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux médecins",
        )
    return current_user

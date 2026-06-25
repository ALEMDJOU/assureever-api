import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


def _get_env_file() -> str:
    """Choisit le fichier .env selon l'environnement."""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production" and os.path.exists(".env.production"):
        return ".env.production"
    return ".env"


class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str

    # JWT / NextAuth
    NEXTAUTH_SECRET: str

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Environnement
    ENVIRONMENT: str = "development"

    # Serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Titre de l'API
    API_TITLE: str = "Sécurité Sociale API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def strip_database_url(cls, v: str) -> str:
        """Supprime les espaces/sauts de ligne parasites."""
        return v.strip()

    class Config:
        env_file = _get_env_file()
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


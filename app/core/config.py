from pydantic_settings import BaseSettings
from functools import lru_cache


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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

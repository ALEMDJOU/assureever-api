from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    # Le pooler Supabase (Supavisor, mode transaction) ne supporte pas les
    # prepared statements côté serveur réutilisés entre requêtes — asyncpg
    # les active par défaut, ce qui casse la connexion. On les désactive.
    # ssl="require" : Neon (et la plupart des Postgres managés) exigent TLS ;
    # on le force ici plutôt que via la query string (sslmode n'est pas
    # compris par asyncpg, qui attend "ssl").
    connect_args={"statement_cache_size": 0, "ssl": "require"},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dépendance FastAPI — injecte une session de base de données."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

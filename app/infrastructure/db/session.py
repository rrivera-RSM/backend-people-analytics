from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from settings import Settings

settings = Settings()
database_url = settings.DATABASE_URL
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # evita conexiones muertas en pools largos
    echo=settings.SQL_ECHO,  # útil en dev; en prod mejor False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para FastAPI.
    Crea una sesión por request y la cierra al final.
    """
    async with AsyncSessionLocal() as session:
        yield session


# (Opcional) Healthcheck rápido de DB (útil para readiness/liveness)
async def db_healthcheck() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

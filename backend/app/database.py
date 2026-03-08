from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.config import settings


def _build_engine():
    kwargs: dict = {"echo": settings.DEBUG, "future": True}

    # SQLite requer check_same_thread=False para funcionar com async
    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}

    return create_async_engine(settings.DATABASE_URL, **kwargs)


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """
    Cria todas as tabelas registradas no metadata.
    Usado apenas em desenvolvimento — produção usa `alembic upgrade head`.
    """
    if settings.ENVIRONMENT == "production":
        return  # Alembic gerencia o schema em produção

    # Importar todos os models para registrá-los no Base.metadata
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

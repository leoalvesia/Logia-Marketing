import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Carregar settings e Base antes de qualquer coisa
from app.config import settings
from app.database import Base
import app.models  # noqa: F401 — registra todos os models no Base.metadata

# ──────────────────────────────────────────────
# Configuração Alembic
# ──────────────────────────────────────────────

alembic_cfg = context.config

if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

# URL do banco — vem do .env via settings.
# Para offline mode (geração de SQL puro), substitui driver async por sync.
def _sync_url() -> str:
    url = settings.DATABASE_URL
    url = url.replace("sqlite+aiosqlite", "sqlite")
    url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return url


alembic_cfg.set_main_option("sqlalchemy.url", _sync_url())

target_metadata = Base.metadata


# ──────────────────────────────────────────────
# Helpers de configuração do contexto
# ──────────────────────────────────────────────

def _is_sqlite() -> bool:
    return settings.DATABASE_URL.startswith("sqlite")


def _configure_context(connection, **extra):
    """
    Configura o contexto de migração.
    render_as_batch=True é obrigatório para SQLite, pois o banco não suporta
    ALTER TABLE diretamente (Alembic usa create-copy-drop internamente).
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=_is_sqlite(),
        compare_type=True,
        **extra,
    )


# ──────────────────────────────────────────────
# Modo offline — gera SQL sem conectar ao banco
# ──────────────────────────────────────────────

def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_is_sqlite(),
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ──────────────────────────────────────────────
# Modo online — conecta e aplica migrations
# ──────────────────────────────────────────────

def do_run_migrations(connection) -> None:
    _configure_context(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # Copia a seção de configuração e sobrescreve a URL com o driver async
    cfg_section = dict(alembic_cfg.get_section(alembic_cfg.config_ini_section, {}))
    cfg_section["sqlalchemy.url"] = settings.DATABASE_URL  # URL com driver async

    connectable = async_engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

"""
conftest.py — Fixtures globais reutilizáveis para toda a suite de testes.

Responsabilidades:
  - db_session: banco SQLite em memória, isolado por teste
  - test_client: TestClient assíncrono do FastAPI
  - mock_pipeline / mock_topic: objetos prontos para uso em testes unitários
  - Patch global do LLM para não gastar tokens nos testes
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app

# ── Models (necessário para registrar os metadados) ───────────────────────────
import app.models  # noqa: F401
from app.models.copy import Copy, CopyChannel, CopyStatus
from app.models.pipeline import Pipeline, PipelineState
from app.models.topic import Topic
from app.models.user import User

# ─────────────────────────────────────────────────────────────────────────────
# Banco de dados em memória
# ─────────────────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Engine SQLite em memória — um novo banco por função de teste."""
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Sessão assíncrona isolada — faz rollback ao final do teste."""
    maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with maker() as session:
        yield session
        await session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI TestClient
# ─────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def test_client(async_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    AsyncClient do httpx apontando para a app FastAPI.
    Substitui a dependência real de DB pela sessão de testes.
    """
    maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override_get_db():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de domínio
# ─────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def mock_user(db_session: AsyncSession) -> User:
    """Usuário básico persistido no banco de testes."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@logia.com",
        hashed_password="hashed_pw_for_tests",
        name="Usuário Teste",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture(scope="function")
async def mock_pipeline(db_session: AsyncSession, mock_user: User) -> Pipeline:
    """
    PipelineSession em estado RESEARCHING — ponto de partida mais comum
    nos testes de fluxo do orquestrador.
    """
    pipeline = Pipeline(
        id=str(uuid.uuid4()),
        user_id=mock_user.id,
        state=PipelineState.RESEARCHING,
    )
    db_session.add(pipeline)
    await db_session.flush()
    return pipeline


@pytest_asyncio.fixture(scope="function")
async def mock_topic(db_session: AsyncSession, mock_pipeline: Pipeline) -> Topic:
    """
    Topic com dados plausíveis e source_url válida — fixture padrão para
    testes que precisam de um tema já selecionado.
    """
    topic = Topic(
        id=str(uuid.uuid4()),
        pipeline_id=mock_pipeline.id,
        user_id=mock_pipeline.user_id,
        title="IA generativa transforma processos de marketing em 2026",
        summary=(
            "Empresas brasileiras adotam ferramentas de IA para automação de "
            "conteúdo, reduzindo em 70% o tempo de produção sem perder qualidade."
        ),
        source_url="https://example.com/article-ia-marketing-2026",
        score=0.92,
        rank=1,
        channels_found=json.dumps(["instagram", "linkedin", "youtube", "twitter"]),
    )
    db_session.add(topic)
    await db_session.flush()
    return topic


# ─────────────────────────────────────────────────────────────────────────────
# Patch global do LLM — evita chamadas reais à API Anthropic/OpenAI
# ─────────────────────────────────────────────────────────────────────────────

# Respostas fake realistas por canal
_FAKE_LLM_RESPONSES: dict[str, str] = {
    "instagram": (
        "A IA está revolucionando o marketing de conteúdo! 🚀\n\n"
        "Empresas que adotaram ferramentas de geração automatizada reduziram "
        "em 70% o tempo de produção — sem abrir mão da qualidade.\n\n"
        "Fonte: example.com/article-ia-marketing-2026\n\n"
        "#MarketingDigital #InteligenciaArtificial #ContentMarketing"
    ),
    "linkedin": (
        "A revolução silenciosa do marketing de conteúdo chegou ao Brasil.\n\n"
        "Nos últimos 6 meses, consultores e pequenas empresas que adotaram IA "
        "para produção de conteúdo relatam uma redução de 70% no tempo gasto — "
        "mantendo a mesma consistência e qualidade.\n\n"
        "Fonte: example.com/article-ia-marketing-2026"
    ),
    "twitter": (
        "🧵 Thread: IA no marketing de conteúdo\n\n"
        "1/ Empresas brasileiras estão economizando 70% do tempo com IA\n"
        "2/ Qualidade mantida — ou melhorada\n"
        "3/ A pergunta não é 'se', é 'quando'\n\n"
        "Fonte: example.com/article-ia-marketing-2026"
    ),
    "youtube": (
        "SCRIPT: A IA Que Está Transformando o Marketing de Conteúdo\n\n"
        "INTRO: Você sabia que empresas estão economizando 70% do tempo "
        "com IA?\n\n"
        "DESENVOLVIMENTO: Vamos explorar como ferramentas de IA estão mudando "
        "a forma como criamos conteúdo...\n\n"
        "CTA: Curta e se inscreva para mais conteúdo sobre IA e marketing!"
    ),
    "email": (
        "ASSUNTO: Como a IA pode reduzir 70% do seu tempo de criação de conteúdo\n\n"
        "Olá,\n\n"
        "Trouxemos um estudo incrível sobre como empresas brasileiras estão "
        "usando IA para transformar seus processos de marketing.\n\n"
        "Clique aqui para ler o artigo completo."
    ),
    "default": "Conteúdo gerado pela IA para fins de teste. Fonte: example.com/test",
}


def _fake_llm_response(channel: str = "default") -> str:
    """Retorna resposta fake para o canal especificado."""
    return _FAKE_LLM_RESPONSES.get(channel, _FAKE_LLM_RESPONSES["default"])


@pytest.fixture(autouse=True)
def patch_llm_apis():
    """
    Patch automático aplicado a TODOS os testes.
    Intercepta chamadas às APIs Anthropic e OpenAI para evitar gasto de tokens.
    Só aplica patches para módulos que estiverem instalados no ambiente.
    """
    fake_ai_message = MagicMock()
    fake_ai_message.content = _fake_llm_response("default")

    fake_ainvoke = AsyncMock(return_value=fake_ai_message)
    fake_invoke = MagicMock(return_value=fake_ai_message)

    fake_anthropic_message = MagicMock()
    fake_anthropic_message.content = [MagicMock(text=_fake_llm_response("default"))]
    fake_create = MagicMock(return_value=fake_anthropic_message)
    fake_acreate = AsyncMock(return_value=fake_anthropic_message)

    # Mapa: (target_path, mock_object) — apenas para módulos instalados
    candidate_patches: list[tuple[str, object]] = [
        ("langchain_anthropic.ChatAnthropic.invoke", fake_invoke),
        ("langchain_anthropic.ChatAnthropic.ainvoke", fake_ainvoke),
        ("langchain_openai.ChatOpenAI.invoke", fake_invoke),
        ("langchain_openai.ChatOpenAI.ainvoke", fake_ainvoke),
        ("anthropic.Anthropic.messages", MagicMock(create=fake_create)),
        ("anthropic.AsyncAnthropic.messages", MagicMock(create=fake_acreate)),
        ("openai.OpenAI.chat", MagicMock(completions=MagicMock(create=fake_create))),
        ("openai.AsyncOpenAI.chat", MagicMock(completions=MagicMock(create=fake_acreate))),
    ]

    active_patches = []
    for target, mock_obj in candidate_patches:
        # Extrai o nome do módulo top-level (ex.: "langchain_anthropic")
        module_name = target.split(".")[0]
        if importlib.util.find_spec(module_name) is not None:
            active_patches.append(patch(target, mock_obj))

    started = [p.start() for p in active_patches]
    yield started
    for p in active_patches:
        p.stop()

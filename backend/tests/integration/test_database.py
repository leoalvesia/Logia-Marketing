"""Testes de integração do banco de dados (SQLite em memória)."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base
import app.models  # noqa: F401 — registrar todos os models

from app.models.user import User
from app.models.pipeline import Pipeline, PipelineState
from app.models.topic import Topic
from app.models.copy import Copy, CopyChannel, CopyStatus
from app.models.art import Art, ArtType
from app.models.social_tokens import SocialToken

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def engine():
    """Engine SQLite em memória — isolado por teste."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _create_user(session: AsyncSession, **kwargs) -> User:
    user = User(
        id=_uuid(),
        email=kwargs.get("email", f"{_uuid()}@example.com"),
        hashed_password="hashed",
        name=kwargs.get("name", "Teste"),
    )
    session.add(user)
    await session.flush()
    return user


async def _create_pipeline(session: AsyncSession, user_id: str) -> Pipeline:
    pipeline = Pipeline(id=_uuid(), user_id=user_id)
    session.add(pipeline)
    await session.flush()
    return pipeline


# ── Testes ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_retrieve_user(session):
    user = await _create_user(session, email="hero@logia.com", name="Hero")
    await session.commit()

    result = await session.get(User, user.id)
    assert result is not None
    assert result.email == "hero@logia.com"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_pipeline_fk_to_user(session):
    user = await _create_user(session)
    pipeline = await _create_pipeline(session, user.id)
    await session.commit()

    result = await session.get(Pipeline, pipeline.id)
    assert result.user_id == user.id
    assert result.state == PipelineState.RESEARCHING


@pytest.mark.asyncio
async def test_pipeline_state_transition(session):
    user = await _create_user(session)
    pipeline = await _create_pipeline(session, user.id)

    pipeline.state = PipelineState.AWAITING_SELECTION
    await session.commit()

    result = await session.get(Pipeline, pipeline.id)
    assert result.state == PipelineState.AWAITING_SELECTION


@pytest.mark.asyncio
async def test_topic_source_url_persisted(session):
    """Garante que source_url nunca é perdida no banco."""
    user = await _create_user(session)
    pipeline = await _create_pipeline(session, user.id)

    source = "https://example.com/artigo-ia-2026"
    topic = Topic(
        id=_uuid(),
        pipeline_id=pipeline.id,
        user_id=user.id,
        title="IA em 2026",
        summary="Tendência relevante",
        source_url=source,
        rank=1,
        score=0.92,
    )
    session.add(topic)
    await session.commit()

    result = await session.get(Topic, topic.id)
    assert result.source_url == source
    assert result.rank == 1
    assert result.score == pytest.approx(0.92)


@pytest.mark.asyncio
async def test_copy_fk_chain(session):
    """Copy referencia pipeline — testar integridade."""
    user = await _create_user(session)
    pipeline = await _create_pipeline(session, user.id)

    copy = Copy(
        id=_uuid(),
        pipeline_id=pipeline.id,
        channel=CopyChannel.INSTAGRAM,
        content='{"caption": "Teste de copy", "hashtags": "#logia"}',
        source_url="https://real-source.com",
    )
    session.add(copy)
    await session.commit()

    result = await session.get(Copy, copy.id)
    assert result.channel == CopyChannel.INSTAGRAM
    assert result.status == CopyStatus.DRAFT
    assert result.source_url == "https://real-source.com"


@pytest.mark.asyncio
async def test_art_fk_to_copy(session):
    user = await _create_user(session)
    pipeline = await _create_pipeline(session, user.id)

    copy = Copy(
        id=_uuid(),
        pipeline_id=pipeline.id,
        channel=CopyChannel.INSTAGRAM,
        content="{}",
        source_url="https://x.com",
    )
    session.add(copy)
    await session.flush()

    art = Art(
        id=_uuid(),
        pipeline_id=pipeline.id,
        copy_id=copy.id,
        art_type=ArtType.THUMBNAIL,
    )
    session.add(art)
    await session.commit()

    result = await session.get(Art, art.id)
    assert result.art_type == ArtType.THUMBNAIL
    assert result.image_urls == "[]"


@pytest.mark.asyncio
async def test_social_token_unique_per_platform(session):
    """Usuário só pode ter 1 token por plataforma — unique constraint."""
    user = await _create_user(session)

    t1 = SocialToken(
        id=_uuid(),
        user_id=user.id,
        platform="instagram",
        access_token="token_1",
    )
    session.add(t1)
    await session.commit()

    t2 = SocialToken(
        id=_uuid(),
        user_id=user.id,
        platform="instagram",
        access_token="token_2_duplicado",
    )
    session.add(t2)
    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_all_tables_exist(engine):
    """Verifica que todas as tabelas foram criadas."""
    expected = {
        "users",
        "pipeline_sessions",
        "topics",
        "copies",
        "arts",
        "monitored_profiles",
        "scheduled_posts",
        "social_tokens",
        "request_logs",
        "ai_usage_logs",
        "nps_feedback",
        "post_feedback",
        "bug_reports",
        "invites",
    }
    async with engine.connect() as conn:
        tables = set(await conn.run_sync(lambda c: inspect(c).get_table_names()))

    assert expected == tables, f"Tabelas faltando: {expected - tables}"

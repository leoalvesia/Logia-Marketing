"""Testes dos endpoints /api/library e /api/settings/profiles."""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth import get_current_user
from app.database import get_db
from app.main import app
from app.models.art import Art, ArtType
from app.models.copy import Copy, CopyChannel, CopyStatus
from app.models.pipeline import Pipeline, PipelineState
from app.models.user import User


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def lib_data(async_engine):
    """Cria e commita dados de teste: usuário, pipeline, copy (DRAFT), art."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    user_id = str(uuid.uuid4())
    pipeline_id = str(uuid.uuid4())
    copy_id = str(uuid.uuid4())
    art_id = str(uuid.uuid4())

    async with maker() as session:
        user = User(
            id=user_id,
            email="lib@test.com",
            hashed_password="hash",
            name="Lib User",
        )
        session.add(user)

        pipeline = Pipeline(
            id=pipeline_id,
            user_id=user_id,
            state=PipelineState.RESEARCHING,
        )
        session.add(pipeline)

        copy = Copy(
            id=copy_id,
            pipeline_id=pipeline_id,
            channel=CopyChannel.INSTAGRAM,
            status=CopyStatus.DRAFT,
            content=json.dumps({"caption": "Teste", "hashtags": ["#ia"]}),
            source_url="https://example.com",
        )
        session.add(copy)

        art = Art(
            id=art_id,
            copy_id=copy_id,
            pipeline_id=pipeline_id,
            art_type=ArtType.STATIC,
            image_urls=json.dumps(["https://example.com/img.png"]),
        )
        session.add(art)

        await session.commit()

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.is_active = True

    return {
        "user_id": user_id,
        "pipeline_id": pipeline_id,
        "copy_id": copy_id,
        "art_id": art_id,
        "mock_user": mock_user,
    }


@pytest_asyncio.fixture
async def lib_client(async_engine, lib_data):
    """AsyncClient autenticado com dados da lib_data já commitados."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_db_override():
        async with maker() as session:
            yield session

    mock_user = lib_data["mock_user"]
    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client, lib_data

    app.dependency_overrides.clear()


# ── GET /copies ───────────────────────────────────────────────────────────────


class TestListCopies:
    @pytest.mark.asyncio
    async def test_retorna_lista_de_copies(self, lib_client):
        client, data = lib_client
        resp = await client.get("/api/library/copies")
        assert resp.status_code == 200
        body = resp.json()
        assert "copies" in body
        assert len(body["copies"]) == 1
        assert body["copies"][0]["id"] == data["copy_id"]

    @pytest.mark.asyncio
    async def test_filtro_channel_valido(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies?channel=instagram")
        assert resp.status_code == 200
        assert len(resp.json()["copies"]) == 1

    @pytest.mark.asyncio
    async def test_filtro_channel_invalido_retorna_400(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies?channel=snapchat")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_filtro_channel_diferente_retorna_vazio(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies?channel=linkedin")
        assert resp.status_code == 200
        assert resp.json()["copies"] == []

    @pytest.mark.asyncio
    async def test_filtro_status_draft(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies?status=draft")
        assert resp.status_code == 200
        assert len(resp.json()["copies"]) == 1

    @pytest.mark.asyncio
    async def test_filtro_status_invalido_retorna_400(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies?status=publicado")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_deleted_copies_excluidas_da_listagem(self, lib_client):
        """Copies com status DELETED não aparecem na listagem."""
        client, data = lib_client
        # Soft delete via endpoint
        await client.delete(f"/api/library/copies/{data['copy_id']}")
        resp = await client.get("/api/library/copies")
        assert resp.json()["copies"] == []

    @pytest.mark.asyncio
    async def test_schema_da_copy(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies")
        c = resp.json()["copies"][0]
        assert set(c.keys()) >= {"id", "pipeline_id", "channel", "status", "content", "source_url", "created_at"}

    @pytest.mark.asyncio
    async def test_content_retornado_como_dict(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/copies")
        c = resp.json()["copies"][0]
        assert isinstance(c["content"], dict)


# ── GET /arts ─────────────────────────────────────────────────────────────────


class TestListArts:
    @pytest.mark.asyncio
    async def test_retorna_lista_de_arts(self, lib_client):
        client, data = lib_client
        resp = await client.get("/api/library/arts")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["arts"]) == 1
        assert body["arts"][0]["id"] == data["art_id"]

    @pytest.mark.asyncio
    async def test_filtro_tipo_static(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/arts?type=static")
        assert resp.status_code == 200
        assert len(resp.json()["arts"]) == 1

    @pytest.mark.asyncio
    async def test_filtro_tipo_carousel_retorna_vazio(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/arts?type=carousel")
        assert resp.status_code == 200
        assert resp.json()["arts"] == []

    @pytest.mark.asyncio
    async def test_filtro_tipo_invalido_retorna_400(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/arts?type=banner")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_schema_da_art(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/arts")
        a = resp.json()["arts"][0]
        assert set(a.keys()) >= {"id", "copy_id", "pipeline_id", "type", "image_urls", "created_at"}

    @pytest.mark.asyncio
    async def test_image_urls_como_lista(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/arts")
        assert isinstance(resp.json()["arts"][0]["image_urls"], list)


# ── GET /posts ────────────────────────────────────────────────────────────────


class TestListPosts:
    @pytest.mark.asyncio
    async def test_retorna_posts_por_pipeline(self, lib_client):
        client, data = lib_client
        resp = await client.get("/api/library/posts")
        assert resp.status_code == 200
        posts = resp.json()["posts"]
        assert len(posts) == 1
        assert posts[0]["pipeline_id"] == data["pipeline_id"]

    @pytest.mark.asyncio
    async def test_post_tem_copies_e_arts(self, lib_client):
        client, _ = lib_client
        resp = await client.get("/api/library/posts")
        post = resp.json()["posts"][0]
        assert len(post["copies"]) == 1
        assert len(post["arts"]) == 1

    @pytest.mark.asyncio
    async def test_sem_pipelines_retorna_vazio(self, async_engine):
        """Usuário sem pipelines recebe lista vazia."""
        maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        user_id = str(uuid.uuid4())
        async with maker() as session:
            session.add(User(id=user_id, email="empty@test.com", hashed_password="h", name="E"))
            await session.commit()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        app.dependency_overrides[get_db] = lambda: (
            maker().__aenter__()
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user

        async def _get_db_override():
            async with maker() as session:
                yield session

        app.dependency_overrides[get_db] = _get_db_override
        app.dependency_overrides[get_current_user] = lambda: mock_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            resp = await client.get("/api/library/posts")

        app.dependency_overrides.clear()
        assert resp.json()["posts"] == []


# ── PATCH /copies/{id}/approve ────────────────────────────────────────────────


class TestApproveCopy:
    @pytest.mark.asyncio
    async def test_approve_muda_status_para_approved(self, lib_client):
        client, data = lib_client
        resp = await client.patch(f"/api/library/copies/{data['copy_id']}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_approve_copy_inexistente_retorna_404(self, lib_client):
        client, _ = lib_client
        resp = await client.patch(f"/api/library/copies/{uuid.uuid4()}/approve")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_copy_de_outro_usuario_retorna_404(self, lib_client):
        """Copy de outro pipeline/usuário não deve ser acessível."""
        client, _ = lib_client
        # ID que não pertence ao usuário logado
        resp = await client.patch(f"/api/library/copies/{uuid.uuid4()}/approve")
        assert resp.status_code == 404


# ── DELETE /copies/{id} ───────────────────────────────────────────────────────


class TestDeleteCopy:
    @pytest.mark.asyncio
    async def test_delete_retorna_204(self, lib_client):
        client, data = lib_client
        resp = await client.delete(f"/api/library/copies/{data['copy_id']}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_faz_soft_delete_status_deleted(self, lib_client):
        client, data = lib_client
        await client.delete(f"/api/library/copies/{data['copy_id']}")
        # Não aparece mais na listagem
        resp = await client.get("/api/library/copies")
        assert all(c["id"] != data["copy_id"] for c in resp.json()["copies"])

    @pytest.mark.asyncio
    async def test_delete_copy_inexistente_retorna_404(self, lib_client):
        client, _ = lib_client
        resp = await client.delete(f"/api/library/copies/{uuid.uuid4()}")
        assert resp.status_code == 404

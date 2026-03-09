"""Testes dos endpoints /api/settings/profiles."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth import get_current_user
from app.database import get_db
from app.main import app
from app.models.user import User

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def settings_data(async_engine):
    """Cria e commita um usuário para os testes de settings."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    user_id = str(uuid.uuid4())

    async with maker() as session:
        session.add(User(id=user_id, email="cfg@test.com", hashed_password="h", name="Cfg"))
        await session.commit()

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.is_active = True
    return {"user_id": user_id, "mock_user": mock_user}


@pytest_asyncio.fixture
async def settings_client(async_engine, settings_data):
    """AsyncClient autenticado para os testes de settings."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_db_override():
        async with maker() as session:
            yield session

    mock_user = settings_data["mock_user"]
    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client, settings_data

    app.dependency_overrides.clear()


# ── POST /settings/profiles ───────────────────────────────────────────────────


class TestAddProfile:
    @pytest.mark.asyncio
    async def test_cria_perfil_retorna_201(self, settings_client):
        client, _ = settings_client
        resp = await client.post(
            "/api/settings/profiles",
            json={
                "platform": "instagram",
                "handle": "@logia_br",
                "url": "https://instagram.com/logia_br",
            },
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_schema_do_perfil_criado(self, settings_client):
        client, _ = settings_client
        resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "linkedin", "handle": "logia-consultoria"},
        )
        body = resp.json()
        assert set(body.keys()) >= {"id", "platform", "handle", "url", "active", "created_at"}

    @pytest.mark.asyncio
    async def test_perfil_criado_com_active_true(self, settings_client):
        client, _ = settings_client
        resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "twitter", "handle": "logia_br"},
        )
        assert resp.json()["active"] is True

    @pytest.mark.asyncio
    async def test_arroba_removido_do_handle(self, settings_client):
        client, _ = settings_client
        resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "instagram", "handle": "@logia_br"},
        )
        assert resp.json()["handle"] == "logia_br"

    @pytest.mark.asyncio
    async def test_plataforma_invalida_retorna_400(self, settings_client):
        client, _ = settings_client
        resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "tiktok", "handle": "logia"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_url_opcional(self, settings_client):
        client, _ = settings_client
        resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "youtube", "handle": "logia_channel"},
        )
        assert resp.status_code == 201
        assert resp.json()["url"] is None


# ── GET /settings/profiles ────────────────────────────────────────────────────


class TestListProfiles:
    @pytest.mark.asyncio
    async def test_lista_vazia_inicialmente(self, settings_client):
        client, _ = settings_client
        resp = await client.get("/api/settings/profiles")
        assert resp.status_code == 200
        assert resp.json()["profiles"] == []

    @pytest.mark.asyncio
    async def test_retorna_perfis_criados(self, settings_client):
        client, _ = settings_client
        await client.post(
            "/api/settings/profiles",
            json={"platform": "instagram", "handle": "p1"},
        )
        await client.post(
            "/api/settings/profiles",
            json={"platform": "linkedin", "handle": "p2"},
        )
        resp = await client.get("/api/settings/profiles")
        assert len(resp.json()["profiles"]) == 2

    @pytest.mark.asyncio
    async def test_lista_com_status_ativo(self, settings_client):
        client, _ = settings_client
        await client.post(
            "/api/settings/profiles",
            json={"platform": "twitter", "handle": "handle_x"},
        )
        profiles = (await client.get("/api/settings/profiles")).json()["profiles"]
        assert all("active" in p for p in profiles)


# ── PATCH /settings/profiles/{id}/toggle ─────────────────────────────────────


class TestToggleProfile:
    @pytest.mark.asyncio
    async def test_toggle_desativa_perfil_ativo(self, settings_client):
        client, _ = settings_client
        create_resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "instagram", "handle": "toggle_me"},
        )
        profile_id = create_resp.json()["id"]

        resp = await client.patch(f"/api/settings/profiles/{profile_id}/toggle")
        assert resp.status_code == 200
        assert resp.json()["active"] is False

    @pytest.mark.asyncio
    async def test_toggle_reativa_perfil_inativo(self, settings_client):
        client, _ = settings_client
        create_resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "instagram", "handle": "toggle_twice"},
        )
        profile_id = create_resp.json()["id"]
        # Desativa
        await client.patch(f"/api/settings/profiles/{profile_id}/toggle")
        # Reativa
        resp = await client.patch(f"/api/settings/profiles/{profile_id}/toggle")
        assert resp.json()["active"] is True

    @pytest.mark.asyncio
    async def test_toggle_perfil_inexistente_retorna_404(self, settings_client):
        client, _ = settings_client
        resp = await client.patch(f"/api/settings/profiles/{uuid.uuid4()}/toggle")
        assert resp.status_code == 404


# ── DELETE /settings/profiles/{id} ───────────────────────────────────────────


class TestDeleteProfile:
    @pytest.mark.asyncio
    async def test_delete_retorna_204(self, settings_client):
        client, _ = settings_client
        create_resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "youtube", "handle": "del_me"},
        )
        profile_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/settings/profiles/{profile_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_remove_da_listagem(self, settings_client):
        client, _ = settings_client
        create_resp = await client.post(
            "/api/settings/profiles",
            json={"platform": "twitter", "handle": "gone"},
        )
        profile_id = create_resp.json()["id"]
        await client.delete(f"/api/settings/profiles/{profile_id}")

        profiles = (await client.get("/api/settings/profiles")).json()["profiles"]
        assert all(p["id"] != profile_id for p in profiles)

    @pytest.mark.asyncio
    async def test_delete_perfil_inexistente_retorna_404(self, settings_client):
        client, _ = settings_client
        resp = await client.delete(f"/api/settings/profiles/{uuid.uuid4()}")
        assert resp.status_code == 404

"""Testes do sistema de convites de beta launch e feature flags."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.invite import Invite
from app.models.user import User


# ── Fixtures ──────────────────────────────────────────────────────────────────

ADMIN_KEY = "test-admin-key-abc123"


@pytest_asyncio.fixture
async def invite_client(async_engine):
    """AsyncClient sem autenticação de usuário (endpoints admin + register)."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_db_override():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override

    with patch.object(settings, "ADMIN_KEY", ADMIN_KEY):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            yield client, maker

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def valid_invite(invite_client):
    """Cria e retorna um convite válido via endpoint admin."""
    client, _ = invite_client
    resp = await client.post(
        "/admin/invites",
        json={"created_by": "admin", "max_uses": 1},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 201
    return resp.json()


# ── Modelo Invite — propriedades ───────────────────────────────────────────────


class TestInviteModel:
    def test_is_expired_sem_data(self):
        invite = Invite(code="x", created_by="a", max_uses=1, uses_count=0)
        assert invite.is_expired is False

    def test_is_expired_data_passada(self):
        invite = Invite(
            code="x",
            created_by="a",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert invite.is_expired is True

    def test_is_expired_data_futura(self):
        invite = Invite(
            code="x",
            created_by="a",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        assert invite.is_expired is False

    def test_is_used_sem_usos(self):
        invite = Invite(code="x", created_by="a", max_uses=1, uses_count=0)
        assert invite.is_used is False

    def test_is_used_com_usos_esgotados(self):
        invite = Invite(code="x", created_by="a", max_uses=1, uses_count=1)
        assert invite.is_used is True

    def test_is_used_multi_use(self):
        invite = Invite(code="x", created_by="a", max_uses=3, uses_count=2)
        assert invite.is_used is False


# ── POST /admin/invites ────────────────────────────────────────────────────────


class TestCreateInvite:
    @pytest.mark.asyncio
    async def test_cria_convite_retorna_201(self, invite_client):
        client, _ = invite_client
        resp = await client.post(
            "/admin/invites",
            json={"created_by": "admin"},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_convite_tem_codigo_uuid(self, invite_client):
        client, _ = invite_client
        resp = await client.post(
            "/admin/invites",
            json={},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        code = resp.json()["code"]
        # Deve ser UUID válido
        uuid.UUID(code)

    @pytest.mark.asyncio
    async def test_convite_status_available(self, invite_client):
        client, _ = invite_client
        resp = await client.post(
            "/admin/invites",
            json={},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert resp.json()["status"] == "available"

    @pytest.mark.asyncio
    async def test_convite_com_expiracao(self, invite_client):
        client, _ = invite_client
        resp = await client.post(
            "/admin/invites",
            json={"expires_in_days": 7},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert resp.json()["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_sem_admin_key_retorna_422(self, invite_client):
        client, _ = invite_client
        resp = await client.post("/admin/invites", json={})
        assert resp.status_code == 422  # header obrigatório ausente

    @pytest.mark.asyncio
    async def test_admin_key_errada_retorna_403(self, invite_client):
        client, _ = invite_client
        resp = await client.post(
            "/admin/invites",
            json={},
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert resp.status_code == 403


# ── GET /admin/invites ─────────────────────────────────────────────────────────


class TestListInvites:
    @pytest.mark.asyncio
    async def test_lista_vazia_inicialmente(self, invite_client):
        client, _ = invite_client
        resp = await client.get("/admin/invites", headers={"X-Admin-Key": ADMIN_KEY})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_lista_convites_criados(self, invite_client):
        client, _ = invite_client
        await client.post("/admin/invites", json={}, headers={"X-Admin-Key": ADMIN_KEY})
        await client.post("/admin/invites", json={}, headers={"X-Admin-Key": ADMIN_KEY})
        resp = await client.get("/admin/invites", headers={"X-Admin-Key": ADMIN_KEY})
        assert resp.json()["total"] == 2

    @pytest.mark.asyncio
    async def test_schema_do_convite(self, invite_client):
        client, _ = invite_client
        await client.post("/admin/invites", json={}, headers={"X-Admin-Key": ADMIN_KEY})
        invites = (
            await client.get("/admin/invites", headers={"X-Admin-Key": ADMIN_KEY})
        ).json()["invites"]
        assert set(invites[0].keys()) >= {
            "id", "code", "created_by", "used_by", "used_at",
            "uses_count", "max_uses", "expires_at", "created_at", "status",
        }


# ── POST /auth/register com invite_code ───────────────────────────────────────


class TestRegisterWithInvite:
    @pytest.mark.asyncio
    async def test_registro_valido_retorna_201(self, invite_client, valid_invite):
        client, _ = invite_client
        with patch("app.routers.auth.send_welcome_email"):
            resp = await client.post(
                "/auth/register",
                json={
                    "email": "novo@test.com",
                    "password": "senha123",
                    "name": "Novo Usuário",
                    "invite_code": valid_invite["code"],
                },
            )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_registro_retorna_token(self, invite_client, valid_invite):
        client, _ = invite_client
        with patch("app.routers.auth.send_welcome_email"):
            resp = await client.post(
                "/auth/register",
                json={
                    "email": "token@test.com",
                    "password": "senha123",
                    "name": "Token User",
                    "invite_code": valid_invite["code"],
                },
            )
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["onboarding_completed"] is False

    @pytest.mark.asyncio
    async def test_codigo_invalido_retorna_404(self, invite_client):
        client, _ = invite_client
        resp = await client.post(
            "/auth/register",
            json={
                "email": "x@test.com",
                "password": "abc",
                "name": "X",
                "invite_code": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_codigo_expirado_retorna_410(self, invite_client, async_engine):
        client, maker = invite_client
        # Inserir convite expirado diretamente no banco
        async with maker() as session:
            expired = Invite(
                id=str(uuid.uuid4()),
                code=str(uuid.uuid4()),
                created_by="admin",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
            session.add(expired)
            await session.commit()
            code = expired.code

        resp = await client.post(
            "/auth/register",
            json={"email": "exp@test.com", "password": "abc", "name": "Exp", "invite_code": code},
        )
        assert resp.status_code == 410

    @pytest.mark.asyncio
    async def test_codigo_ja_usado_retorna_409(self, invite_client, async_engine):
        client, maker = invite_client
        # Inserir convite já esgotado
        async with maker() as session:
            used = Invite(
                id=str(uuid.uuid4()),
                code=str(uuid.uuid4()),
                created_by="admin",
                max_uses=1,
                uses_count=1,
            )
            session.add(used)
            await session.commit()
            code = used.code

        resp = await client.post(
            "/auth/register",
            json={"email": "used@test.com", "password": "abc", "name": "Used", "invite_code": code},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_convite_marcado_como_usado_apos_registro(self, invite_client, valid_invite, async_engine):
        client, maker = invite_client
        with patch("app.routers.auth.send_welcome_email"):
            await client.post(
                "/auth/register",
                json={
                    "email": "mark@test.com",
                    "password": "abc",
                    "name": "Mark",
                    "invite_code": valid_invite["code"],
                },
            )

        # Segundo registro com o mesmo código deve retornar 409
        with patch("app.routers.auth.send_welcome_email"):
            resp2 = await client.post(
                "/auth/register",
                json={
                    "email": "mark2@test.com",
                    "password": "abc",
                    "name": "Mark2",
                    "invite_code": valid_invite["code"],
                },
            )
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_email_duplicado_retorna_400(self, invite_client, async_engine):
        client, maker = invite_client
        # Criar dois convites
        r1 = await client.post("/admin/invites", json={}, headers={"X-Admin-Key": ADMIN_KEY})
        r2 = await client.post("/admin/invites", json={}, headers={"X-Admin-Key": ADMIN_KEY})
        code1 = r1.json()["code"]
        code2 = r2.json()["code"]

        with patch("app.routers.auth.send_welcome_email"):
            await client.post(
                "/auth/register",
                json={"email": "dup@test.com", "password": "abc", "name": "Dup", "invite_code": code1},
            )
            resp = await client.post(
                "/auth/register",
                json={"email": "dup@test.com", "password": "abc", "name": "Dup2", "invite_code": code2},
            )
        assert resp.status_code == 400


# ── Feature Flags ──────────────────────────────────────────────────────────────


class TestFeatureFlags:
    @pytest.mark.asyncio
    async def test_list_features_retorna_flags(self, invite_client):
        client, _ = invite_client
        resp = await client.get("/admin/features", headers={"X-Admin-Key": ADMIN_KEY})
        assert resp.status_code == 200
        flags = resp.json()["flags"]
        assert set(flags.keys()) == {
            "carousel_agent", "thumbnail_agent", "linkedin_publish", "youtube_research"
        }

    @pytest.mark.asyncio
    async def test_public_features_sem_autenticacao(self, invite_client):
        client, _ = invite_client
        resp = await client.get("/api/features")
        assert resp.status_code == 200
        assert "flags" in resp.json()

    @pytest.mark.asyncio
    async def test_toggle_feature_valido(self, invite_client):
        client, _ = invite_client
        resp = await client.patch(
            "/admin/features/carousel_agent",
            json={"enabled": True},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    @pytest.mark.asyncio
    async def test_toggle_feature_invalido_retorna_404(self, invite_client):
        client, _ = invite_client
        resp = await client.patch(
            "/admin/features/feature_inexistente",
            json={"enabled": True},
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert resp.status_code == 404


# ── GET /auth/me/onboarding ───────────────────────────────────────────────────


class TestOnboardingEndpoint:
    @pytest.mark.asyncio
    async def test_onboarding_nao_completado_por_padrao(self, invite_client, valid_invite):
        client, _ = invite_client
        with patch("app.routers.auth.send_welcome_email"):
            reg_resp = await client.post(
                "/auth/register",
                json={
                    "email": "ob@test.com",
                    "password": "abc",
                    "name": "Ob",
                    "invite_code": valid_invite["code"],
                },
            )
        assert reg_resp.json()["user"]["onboarding_completed"] is False

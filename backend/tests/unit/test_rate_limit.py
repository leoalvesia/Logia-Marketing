"""Testes do middleware de rate limiting."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth import get_current_user
from app.database import get_db
from app.main import app
from app.middleware.rate_limit import (
    _check_and_increment,
    _extract_user_id,
    _match_limit,
)
from app.models.user import User

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_mock_user(user_id: str = "user-rl-test") -> MagicMock:
    mock = MagicMock(spec=User)
    mock.id = user_id
    mock.is_active = True
    return mock


def _auth_header(token: str = "mock-token") -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Testes unitários dos helpers ───────────────────────────────────────────────


class TestMatchLimit:
    def test_pipeline_start_configurado(self):
        result = _match_limit("POST", "/api/pipeline/start")
        assert result is not None
        limit, window, key_by = result
        assert limit == 20
        assert window == 3600

    def test_select_topic_configurado(self):
        result = _match_limit("POST", "/api/pipeline/abc-123/select-topic")
        assert result is not None
        limit, window, key_by = result
        assert limit == 100

    def test_approve_copy_configurado(self):
        result = _match_limit("POST", "/api/pipeline/abc-123/approve-copy")
        assert result is not None

    def test_get_nao_limitado(self):
        assert _match_limit("GET", "/api/library/copies") is None

    def test_health_nao_limitado(self):
        assert _match_limit("GET", "/health") is None

    def test_endpoint_desconhecido_nao_limitado(self):
        assert _match_limit("POST", "/api/settings/profiles") is None


class TestExtractUserId:
    def test_sem_header_retorna_none(self):
        req = MagicMock()
        req.headers = {}
        assert _extract_user_id(req) is None

    def test_header_invalido_retorna_none(self):
        req = MagicMock()
        req.headers = {"Authorization": "Basic xxx"}
        assert _extract_user_id(req) is None

    def test_jwt_valido_retorna_sub(self):
        from jose import jwt

        token = jwt.encode(
            {"sub": "user-42", "exp": int(time.time()) + 3600},
            "qualquer-chave",
            algorithm="HS256",
        )
        req = MagicMock()
        req.headers = {"Authorization": f"Bearer {token}"}
        assert _extract_user_id(req) == "user-42"

    def test_token_malformado_retorna_none(self):
        req = MagicMock()
        req.headers = {"Authorization": "Bearer nao-e-um-jwt"}
        assert _extract_user_id(req) is None


# ── Testes de _check_and_increment ─────────────────────────────────────────────


class TestCheckAndIncrement:
    async def test_redis_indisponivel_fail_open(self):
        """Sem Redis, rate limit nunca bloqueia (fail open)."""
        # O circuit-breaker pode estar aberto — nesse caso retorna False (pass)
        result = await _check_and_increment("test-key", limit=1, window=60)
        assert result is False  # fail open

    async def test_dentro_do_limite(self):
        """Mock Redis: contador abaixo do limite → não bloqueia."""
        # pipeline() é síncrono → MagicMock; incr/expire/execute são async → AsyncMock
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[1, True])

        mock_client = MagicMock()  # NÃO AsyncMock — pipeline() é síncrono
        mock_client.pipeline.return_value = mock_pipe

        with (
            patch("app.middleware.rate_limit._rl_circuit_open", return_value=False),
            patch("app.middleware.rate_limit._get_rl_client", return_value=mock_client),
        ):
            result = await _check_and_increment("test:key", limit=10, window=3600)

        assert result is False  # 1 <= 10, não excedeu

    async def test_acima_do_limite(self):
        """Mock Redis: contador acima do limite → bloqueia."""
        mock_pipe = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[11, True])

        mock_client = MagicMock()  # NÃO AsyncMock — pipeline() é síncrono
        mock_client.pipeline.return_value = mock_pipe

        with (
            patch("app.middleware.rate_limit._rl_circuit_open", return_value=False),
            patch("app.middleware.rate_limit._get_rl_client", return_value=mock_client),
        ):
            result = await _check_and_increment("test:key", limit=10, window=3600)

        assert result is True  # 11 > 10, excedeu


# ── Testes de integração via HTTP ──────────────────────────────────────────────


@pytest.fixture
async def rl_client(async_engine):
    """Cliente HTTP com DB override e rate limit mockado."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    mock_user = _make_mock_user()

    async def _get_db_override():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client, mock_user

    app.dependency_overrides.clear()


class TestRateLimitHTTP:
    async def test_request_sem_token_nao_bloqueado(self, rl_client):
        """Requests sem Bearer token passam (serão rejeitados pelo auth, não pelo RL)."""
        client, _ = rl_client
        with patch("app.middleware.rate_limit._check_and_increment", return_value=False):
            resp = await client.get("/health")
        assert resp.status_code != 429

    async def test_request_dentro_do_limite_passa(self, rl_client):
        """Requests dentro do limite retornam o status normal do endpoint."""
        client, _ = rl_client
        with patch("app.middleware.rate_limit._check_and_increment", return_value=False):
            resp = await client.post(
                "/api/pipeline/start",
                json={"channels": ["instagram"]},
            )
        assert resp.status_code != 429

    async def test_request_acima_do_limite_retorna_429(self, rl_client):
        """Requests acima do limite retornam 429 com payload correto."""
        client, _ = rl_client

        from jose import jwt as _jwt

        token = _jwt.encode(
            {"sub": "user-rl-test"},
            "dev-secret-change-in-production",
            algorithm="HS256",
        )

        with patch("app.middleware.rate_limit._check_and_increment", return_value=True):
            resp = await client.post(
                "/api/pipeline/start",
                headers={"Authorization": f"Bearer {token}"},
                json={"channels": ["instagram"]},
            )

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "rate_limit"
        assert "retry_after" in body
        assert int(resp.headers["Retry-After"]) > 0

    async def test_health_nunca_bloqueado(self, rl_client):
        """Health check nunca passa pelo rate limit (não está na lista)."""
        client, _ = rl_client
        # Mesmo que _check_and_increment retornasse True (não vai ser chamado),
        # /health não está na lista de endpoints limitados.
        resp = await client.get("/health")
        assert resp.status_code != 429

    async def test_endpoint_get_nao_bloqueado(self, rl_client):
        """GET endpoints não têm rate limit configurado."""
        client, _ = rl_client
        with patch("app.middleware.rate_limit._check_and_increment", return_value=True):
            # Mesmo com check retornando True, GET /copies não é verificado
            resp = await client.get("/api/library/copies")
        # 200 porque o endpoint GET não passa pelo check
        assert resp.status_code == 200

"""Testes do endpoint /health."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import get_db
from app.main import app


@pytest.fixture
async def health_client(async_engine):
    """Cliente HTTP com DB override para testes do /health."""
    maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_db_override():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client

    app.dependency_overrides.clear()


class TestHealthEndpoint:
    async def test_retorna_200_com_db_ok(self, health_client):
        """Com banco em memória disponível, deve retornar 200."""
        resp = await health_client.get("/health")
        assert resp.status_code == 200

    async def test_schema_completo(self, health_client):
        """Resposta deve conter todos os campos esperados."""
        resp = await health_client.get("/health")
        body = resp.json()
        assert "status" in body
        assert "database" in body
        assert "redis" in body
        assert "celery" in body
        assert "uptime_seconds" in body

    async def test_database_ok(self, health_client):
        """Com banco de teste disponível, database deve ser 'ok'."""
        resp = await health_client.get("/health")
        assert resp.json()["database"]["status"] == "ok"

    async def test_uptime_nao_negativo(self, health_client):
        """uptime_seconds deve ser >= 0."""
        resp = await health_client.get("/health")
        assert resp.json()["uptime_seconds"] >= 0

    async def test_status_healthy_quando_db_ok(self, health_client):
        """status deve ser 'healthy' quando DB está ok."""
        resp = await health_client.get("/health")
        assert resp.json()["status"] == "healthy"

    async def test_celery_workers_e_inteiro(self, health_client):
        """celery deve conter workers_online como inteiro (0 quando workers não estão rodando)."""
        resp = await health_client.get("/health")
        assert isinstance(resp.json()["celery"]["workers_online"], int)
        assert resp.json()["celery"]["workers_online"] >= 0

    async def test_redis_campo_presente(self, health_client):
        """redis deve ter status 'ok' ou 'error'."""
        resp = await health_client.get("/health")
        assert resp.json()["redis"]["status"] in ("ok", "error")

    async def test_retorna_503_quando_db_falha(self, async_engine):
        """Quando DB falha, deve retornar 503."""

        async def _failing_db():
            from sqlalchemy.ext.asyncio import AsyncSession
            from sqlalchemy.exc import OperationalError

            # Sessão que falha no execute
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.execute = AsyncMock(side_effect=OperationalError("DB down", None, None))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            yield mock_session

        app.dependency_overrides[get_db] = _failing_db

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            resp = await client.get("/health")

        app.dependency_overrides.clear()

        assert resp.status_code == 503
        body = resp.json()
        assert body["database"]["status"] == "error"
        assert body["status"] == "degraded"

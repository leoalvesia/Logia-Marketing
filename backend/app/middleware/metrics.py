"""Middleware de métricas HTTP — registra latência de cada request no banco.

Persiste {endpoint, method, duration_ms, status_code, timestamp} na tabela
``request_logs`` de forma assíncrona (fire-and-forget) para não impactar
a latência de resposta.

Emite ``logger.warning`` para requests com duration_ms > 500 ms.
"""

from __future__ import annotations

import asyncio
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import AsyncSessionLocal
from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)

SLOW_THRESHOLD_MS: int = 500


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware que registra métricas de tempo de resposta por endpoint."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        endpoint = request.url.path
        method = request.method
        status_code = response.status_code

        if duration_ms > SLOW_THRESHOLD_MS:
            logger.warning(
                "Slow request: %s %s → %d ms (status=%d)",
                method,
                endpoint,
                duration_ms,
                status_code,
            )

        # Fire-and-forget: não bloqueia a resposta ao cliente
        try:
            asyncio.get_running_loop().create_task(
                _persist_log(endpoint, method, duration_ms, status_code)
            )
        except RuntimeError:
            pass  # sem event loop rodando (context ASGI sempre tem um)

        return response


async def _persist_log(endpoint: str, method: str, duration_ms: int, status_code: int) -> None:
    """Salva o registro de métricas na tabela request_logs."""
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                RequestLog(
                    endpoint=endpoint,
                    method=method,
                    duration_ms=duration_ms,
                    status_code=status_code,
                )
            )
            await db.commit()
    except Exception as exc:
        # Silencioso: métricas nunca devem quebrar a aplicação
        logger.debug("MetricsMiddleware: falha ao persistir log: %s", exc)

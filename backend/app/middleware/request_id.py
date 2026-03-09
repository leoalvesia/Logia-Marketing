"""
Middleware que gera um X-Request-ID único por requisição e o injeta
no contexto do structlog (disponível em todos os logs do request).
"""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Respeita header existente (útil quando Caddy/proxy upstream já gera)
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Armazena no estado da requisição (acessível nos endpoints)
        request.state.request_id = request_id

        # Injeta no contexto do structlog para todos os logs deste request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)

        # Propaga o ID na resposta para correlação no frontend/logs externos
        response.headers["X-Request-ID"] = request_id
        return response

"""Middleware de Cache-Control HTTP.

Endpoints públicos/estáticos: Cache-Control: public, max-age=60
Endpoints autenticados:       Cache-Control: private, no-store
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_PUBLIC_PATHS: frozenset[str] = frozenset({
    "/health",
    "/openapi.json",
    "/docs",
    "/redoc",
})


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.method == "GET":
            if request.url.path in _PUBLIC_PATHS:
                response.headers["Cache-Control"] = "public, max-age=60"
            elif "Authorization" in request.headers:
                response.headers.setdefault("Cache-Control", "private, no-store")
        return response

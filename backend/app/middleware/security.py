"""Middleware de headers de segurança HTTP (OWASP / defense-in-depth).

Aplicado a todas as respostas da API FastAPI.
Headers duplicados com Caddy são inofensivos — Caddy pode sobrescrever.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Content-Security-Policy para a API (respostas JSON).
# A CSP do frontend HTML é gerenciada pelo nginx.conf / Caddyfile.
_CSP = (
    "default-src 'none'; "
    "connect-src 'self' wss://app.logia.com.br https://app.logia.com.br; "
    "frame-ancestors 'none'"
)

_SECURITY_HEADERS: dict[str, str] = {
    # Impede MIME-type sniffing (CVE genérico de XSS via upload)
    "X-Content-Type-Options": "nosniff",
    # Impede clickjacking via iframe
    "X-Frame-Options": "DENY",
    # Filtro XSS legado (browsers antigos; browsers modernos ignoram)
    "X-XSS-Protection": "1; mode=block",
    # HSTS: forçar HTTPS por 1 ano
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    # CSP restritiva para a API
    "Content-Security-Policy": _CSP,
    # Limitar referrer vazado em requests cross-origin
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Desabilitar features desnecessárias para a API
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

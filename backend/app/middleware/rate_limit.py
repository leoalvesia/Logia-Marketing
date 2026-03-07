"""Middleware de rate limiting baseado em Redis (fixed-window).

Limites configurados (revisão final de segurança):
  POST /auth/login                          →   5 req / min    por IP   (anti-brute-force)
  POST /auth/register                       →   3 req / hora   por IP   (anti-spam de contas)
  POST /api/pipeline/start                  →  20 req / hora   por usuário
  POST /api/pipeline/*/select-topic         → 100 req / hora   por usuário (agentes copy IA)
  POST /api/pipeline/*/approve-copy         → 100 req / hora   por usuário (agentes copy IA)
  POST /api/pipeline/*/approve-art          →  20 req / hora   por usuário (agentes arte)
  POST /feedback/*                          →  10 req / dia    por usuário (anti-spam feedback)

Bloqueio de IP:
  IP bloqueado por 24h após 100 tentativas de login falhas em 1 hora.
  Chamar track_login_failure(ip) no router de auth quando login retornar 401.

Fail-open: quando Redis está indisponível, as requisições passam normalmente.
Circuit-breaker: após 1ª falha de conexão, Redis desabilitado por 30 s.
"""
from __future__ import annotations

import fnmatch
import time
from typing import Optional

import redis.asyncio as aioredis
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# ── Configuração de limites ────────────────────────────────────────────────────
# Tupla: (padrão glob "METHOD:/path/*", limite, janela_segundos, chave_por)
# chave_por: "user" = user_id do JWT | "ip" = IP do cliente
_LIMITS: list[tuple[str, int, int, str]] = [
    ("POST:/auth/login",                         5,     60, "ip"),    # 5/min por IP
    ("POST:/auth/register",                      3,   3600, "ip"),    # 3/hora por IP
    ("POST:/api/pipeline/start",                20,   3600, "user"),  # 20/h por usuário
    ("POST:/api/pipeline/*/select-topic",      100,   3600, "user"),  # 100/h copy agents
    ("POST:/api/pipeline/*/approve-copy",      100,   3600, "user"),  # 100/h copy agents
    ("POST:/api/pipeline/*/approve-art",        20,   3600, "user"),  # 20/h art agents
    ("POST:/feedback/*",                        10,  86400, "user"),  # 10/dia feedback
]

# IP block após falhas de login repetidas
_LOGIN_FAIL_LIMIT = 100          # falhas máximas em 1 hora
_LOGIN_FAIL_WINDOW_S = 3600      # janela de contagem (1 hora)
_LOGIN_BLOCK_TTL_S = 86400       # duração do bloqueio (24 horas)

# ── Redis client com circuit-breaker próprio ───────────────────────────────────

_rl_client: Optional[aioredis.Redis] = None
_rl_open_until: float = 0.0
_RL_COOLDOWN_S: float = 30.0


def _rl_circuit_open() -> bool:
    return time.monotonic() < _rl_open_until


def _trip_rl_circuit() -> None:
    global _rl_open_until
    _rl_open_until = time.monotonic() + _RL_COOLDOWN_S


def _get_rl_client() -> aioredis.Redis:
    global _rl_client
    if _rl_client is None:
        _rl_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
        )
    return _rl_client


# ── Helpers internos ──────────────────────────────────────────────────────────


def _match_limit(method: str, path: str) -> Optional[tuple[int, int, str]]:
    """Retorna (limit, window_seconds, key_by) para o endpoint, ou None."""
    key = f"{method}:{path}"
    for pattern, limit, window, key_by in _LIMITS:
        if fnmatch.fnmatch(key, pattern):
            return limit, window, key_by
    return None


def _extract_user_id(request: Request) -> Optional[str]:
    """Extrai user_id do JWT sem validar assinatura (apenas para chave de RL)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        claims = jwt.get_unverified_claims(token)
        return claims.get("sub")
    except Exception:
        return None


def _client_ip(request: Request) -> str:
    """IP real do cliente, respeitando X-Forwarded-For do Caddy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_and_increment(redis_key: str, limit: int, window: int) -> bool:
    """Incrementa contador e retorna True se o limite foi excedido.

    Fixed-window: bucket = floor(unix_time / window).
    Fail-open (False) quando Redis está indisponível.
    """
    if _rl_circuit_open():
        return False
    try:
        client = _get_rl_client()
        bucket = int(time.time()) // window
        key = f"{redis_key}:{bucket}"
        pipe = client.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, window)
        results = await pipe.execute()
        return results[0] > limit
    except Exception as exc:
        logger.debug("rate_limit_redis_error", error=str(exc))
        _trip_rl_circuit()
        return False


async def _is_ip_blocked(ip: str) -> bool:
    """Verifica se o IP está na blocklist (após 100 falhas de login)."""
    if _rl_circuit_open():
        return False
    try:
        client = _get_rl_client()
        return bool(await client.exists(f"logia:rl:ip_blocked:{ip}"))
    except Exception:
        return False  # fail-open


# ── API pública para o auth router ───────────────────────────────────────────


async def track_login_failure(ip: str) -> None:
    """Registra falha de login por IP.

    Bloqueia o IP por 24h após 100 falhas em 1 hora.
    Chamar no router de auth quando login retornar 401.
    """
    if _rl_circuit_open():
        return
    try:
        client = _get_rl_client()
        bucket = int(time.time()) // _LOGIN_FAIL_WINDOW_S
        fail_key = f"logia:rl:login_fail:{ip}:{bucket}"

        pipe = client.pipeline()
        await pipe.incr(fail_key)
        await pipe.expire(fail_key, _LOGIN_FAIL_WINDOW_S)
        results = await pipe.execute()
        count = results[0]

        if count >= _LOGIN_FAIL_LIMIT:
            block_key = f"logia:rl:ip_blocked:{ip}"
            await client.set(block_key, "1", ex=_LOGIN_BLOCK_TTL_S)
            logger.warning(
                "ip_blocked",
                ip=ip,
                failures=count,
                block_ttl_h=_LOGIN_BLOCK_TTL_S // 3600,
            )
    except Exception as exc:
        logger.debug("track_login_failure_error", error=str(exc))
        _trip_rl_circuit()


# ── Middleware ─────────────────────────────────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting por user/IP + endpoint via Redis (fixed-window)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = _client_ip(request)

        # 1. Verificar se IP está bloqueado (somente em endpoints de auth)
        if request.url.path.startswith("/auth") and await _is_ip_blocked(ip):
            logger.warning("ip_blocked_request", ip=ip, path=request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "ip_blocked",
                    "detail": "IP temporariamente bloqueado por múltiplas tentativas falhas",
                    "retry_after": _LOGIN_BLOCK_TTL_S,
                },
                headers={"Retry-After": str(_LOGIN_BLOCK_TTL_S)},
            )

        # 2. Verificar rate limits configurados
        match = _match_limit(request.method, request.url.path)
        if match is None:
            return await call_next(request)

        limit, window, key_by = match

        if key_by == "ip":
            rl_key = f"logia:rl:{ip}:{request.method}:{request.url.path}"
        else:
            user_id = _extract_user_id(request)
            if not user_id:
                # Sem token — autenticação vai rejeitar em seguida
                return await call_next(request)
            rl_key = f"logia:rl:{user_id}:{request.method}:{request.url.path}"

        exceeded = await _check_and_increment(rl_key, limit, window)
        if exceeded:
            logger.warning(
                "rate_limit_exceeded",
                key_by=key_by,
                method=request.method,
                path=request.url.path,
                window_s=window,
            )
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit", "retry_after": window},
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)

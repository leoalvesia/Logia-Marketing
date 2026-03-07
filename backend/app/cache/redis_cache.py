"""Cache Redis com graceful degradation e circuit-breaker.

Quando o Redis não está disponível, todas as funções falham silenciosamente.
Um circuit-breaker simples desabilita tentativas por 30 s após a primeira
falha de conexão, evitando overhead de timeout em cada request.

Uso:
    from app.cache.redis_cache import cache_get, cache_set, cache_invalidate

    cached = await cache_get("logia:copies:user123:ch=instagram:p=1:pp=20")
    if cached:
        return cached
    ...
    await cache_set(key, data, ttl=60)
    await cache_invalidate("logia:copies:user123:*")
"""
from __future__ import annotations

import json
import logging
import time
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio.client import Redis

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Redis] = None

# Circuit-breaker: tempo Unix (monotônico) até quando o Redis está desabilitado
_circuit_open_until: float = 0.0
_CIRCUIT_COOLDOWN_S: float = 30.0  # volta a tentar após 30 s


def _is_open() -> bool:
    """Retorna True se o circuit-breaker estiver aberto (Redis indisponível)."""
    return time.monotonic() < _circuit_open_until


def _trip_circuit() -> None:
    """Abre o circuit-breaker por _CIRCUIT_COOLDOWN_S segundos."""
    global _circuit_open_until
    _circuit_open_until = time.monotonic() + _CIRCUIT_COOLDOWN_S


def _get_client() -> Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
        )
    return _client


async def cache_get(key: str) -> Optional[dict]:
    """Retorna o valor cacheado ou None se ausente/indisponível."""
    if _is_open():
        return None
    try:
        data = await _get_client().get(key)
        return json.loads(data) if data else None
    except Exception as exc:
        logger.debug("cache_get(%s) falhou — abrindo circuit-breaker: %s", key, exc)
        _trip_circuit()
        return None


async def cache_set(key: str, value: dict, ttl: int = 300) -> None:
    """Persiste value no Redis com TTL em segundos. Falha silenciosamente."""
    if _is_open():
        return
    try:
        await _get_client().setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("cache_set(%s) falhou — abrindo circuit-breaker: %s", key, exc)
        _trip_circuit()


async def cache_invalidate(pattern: str) -> None:
    """Remove todas as chaves que correspondem ao padrão glob.

    Usa KEYS — adequado para volumes pequenos de cache (dev/MVP).
    Em produção com grande volume, substituir por SCAN iterativo.
    """
    if _is_open():
        return
    try:
        client = _get_client()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.debug("cache_invalidate(%s) falhou — abrindo circuit-breaker: %s", pattern, exc)
        _trip_circuit()

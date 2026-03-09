import asyncio
import time
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings, validate_production_config
from app.database import engine, get_db, init_db
from app.logger import configure_logging, get_logger
from app.middleware.cache_control import CacheControlMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.features import get_flags
from app.routers import account as account_router
from app.routers import admin as admin_router
from app.routers import auth, feedback, library, pipeline
from app.routers import costs as costs_router
from app.routers import invites as invites_router
from app.routers import settings as settings_router
from app.ws_manager import manager

logger = get_logger(__name__)

# Instante de início — usado pelo /health para calcular uptime
_start_time: float = time.time()


# ──────────────────────────────────────────────
# Sentry — inicializar antes de criar o app
# ──────────────────────────────────────────────

_SENSITIVE_FIELDS = frozenset(
    {
        "access_token",
        "refresh_token",
        "password",
        "api_key",
        "secret_key",
        "token",
        "authorization",
        "cookie",
        "resend_api_key",
        "anthropic_api_key",
        "openai_api_key",
        "stability_ai_key",
        "apify_token",
        "rapidapi_key",
    }
)


def _scrub_sensitive_data(event: dict, hint: dict) -> dict:
    """Remove campos sensíveis antes de enviar ao Sentry."""

    def _scrub(obj):
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if k.lower() in _SENSITIVE_FIELDS else _scrub(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(i) for i in obj]
        return obj

    if "request" in event:
        event["request"] = _scrub(event["request"])
    if "extra" in event:
        event["extra"] = _scrub(event["extra"])
    return event


def _traces_sampler(sampling_context: dict) -> float:
    """Exclui /health do tracing para não inflar quota."""
    name = sampling_context.get("transaction_context", {}).get("name", "")
    if name.endswith("/health"):
        return 0.0
    return 0.1


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=f"logia@{settings.BUILD_SHA}",
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            CeleryIntegration(monitor_beat_tasks=True),
        ],
        traces_sampler=_traces_sampler,
        profiles_sample_rate=0.1,
        before_send=_scrub_sensitive_data,
    )


# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    _start_time = time.time()
    configure_logging()
    validate_production_config()  # exit(1) se config incompleta em produção
    await init_db()
    logger.info("startup", version=settings.BUILD_SHA, environment=settings.ENVIRONMENT)
    yield
    logger.info("shutdown")


# ──────────────────────────────────────────────
# App
# ──────────────────────────────────────────────

_is_prod = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="Logia Marketing Platform API",
    version="2.0.0",
    description="Plataforma de criação e distribuição de conteúdo com IA",
    lifespan=lifespan,
    # Desabilitar documentação interativa em produção (A05 — Security Misconfiguration)
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

# Middlewares — adicionados de dentro para fora (último adicionado = mais externo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(RequestIdMiddleware)  # mais externo — gera ID antes de tudo

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(account_router.router, prefix="/account", tags=["account"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(admin_router.router, prefix="", tags=["admin"])
app.include_router(invites_router.router, prefix="/admin", tags=["admin"])
app.include_router(costs_router.router, prefix="/admin/costs", tags=["admin"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])


# ──────────────────────────────────────────────
# Health check expandido
# ──────────────────────────────────────────────


@app.get("/api/features", tags=["features"])
async def public_features() -> dict:
    """Expõe feature flags para o frontend (sem autenticação)."""
    return {"flags": get_flags()}


@app.get("/health", tags=["health"])
async def health(db: AsyncSession = Depends(get_db)):
    """Health check detalhado — DB pool, Redis, filas Celery, uptime, versão."""
    uptime = int(time.time() - _start_time)

    # ── Banco de dados (pool stats + query time) ─────────────────────────────
    db_info: dict = {"status": "error"}
    try:
        t0 = time.perf_counter()
        await db.execute(text("SELECT 1"))
        query_ms = round((time.perf_counter() - t0) * 1000, 1)

        pool = engine.sync_engine.pool
        db_info = {
            "status": "ok",
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "query_time_ms": query_ms,
        }
    except Exception as exc:
        logger.warning("health_db_error", error=str(exc))

    # ── Redis (ping + memória) ───────────────────────────────────────────────
    redis_info: dict = {"status": "error"}
    try:
        from app.cache.redis_cache import _get_client

        client = _get_client()
        await client.ping()
        mem = await client.info("memory")
        redis_info = {
            "status": "ok",
            "memory_mb": round(mem["used_memory"] / 1_048_576, 1),
        }
    except Exception as exc:
        logger.warning("health_redis_error", error=str(exc))

    # ── Celery (workers + filas via Redis LLEN) ──────────────────────────────
    celery_info: dict = {"status": "error", "workers_online": 0}
    try:
        from app.cache.redis_cache import _get_client
        from app.celery_app import celery_app as _celery

        def _inspect() -> int:
            pong = _celery.control.inspect(timeout=0.5).ping()
            return len(pong) if pong else 0

        loop = asyncio.get_event_loop()
        workers = await asyncio.wait_for(loop.run_in_executor(None, _inspect), timeout=1.0)

        client = _get_client()
        queue_copy, queue_art, queue_research = await asyncio.gather(
            client.llen("copy"),
            client.llen("art"),
            client.llen("research"),
            return_exceptions=True,
        )

        celery_info = {
            "status": "ok",
            "workers_online": workers,
            "queue_copy": queue_copy if isinstance(queue_copy, int) else 0,
            "queue_art": queue_art if isinstance(queue_art, int) else 0,
            "queue_research": queue_research if isinstance(queue_research, int) else 0,
        }
    except Exception as exc:
        logger.warning("health_celery_error", error=str(exc))

    # ── last_deploy (escrito pelo script de deploy no VPS) ───────────────────
    last_deploy: str | None = None
    try:
        import pathlib

        ts_file = pathlib.Path("/app/.deploy_ts")
        if ts_file.exists():
            last_deploy = ts_file.read_text().strip()
    except Exception:
        pass

    # ── Resultado ────────────────────────────────────────────────────────────
    is_healthy = db_info["status"] == "ok"
    payload = {
        "status": "healthy" if is_healthy else "degraded",
        "version": settings.BUILD_SHA,
        "uptime_seconds": uptime,
        "database": db_info,
        "redis": redis_info,
        "celery": celery_info,
        "last_deploy": last_deploy,
    }

    if not is_healthy:
        return JSONResponse(status_code=503, content=payload)
    return payload


@app.websocket("/ws/pipeline/{session_id}")
async def pipeline_ws(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            await websocket.receive_text()  # keep-alive
    except WebSocketDisconnect:
        manager.disconnect(session_id)

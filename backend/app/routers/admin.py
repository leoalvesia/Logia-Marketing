"""Endpoints do painel de administração de produção.

Admin (X-Admin-Key):
  GET /admin/metrics   → KPIs completos: sistema, usuários, produto, custos IA

Público:
  GET /version         → versão semântica + deploy timestamp
"""

from __future__ import annotations

import asyncio
import statistics
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.version import __version__

router = APIRouter()


# ── Admin auth ─────────────────────────────────────────────────────────────────


async def _require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if not settings.ADMIN_KEY:
        raise HTTPException(status_code=503, detail="ADMIN_KEY não configurado")
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")


# ── /version (público) ─────────────────────────────────────────────────────────


@router.get("/version", tags=["version"])
async def get_version() -> dict:
    """Versão semântica da aplicação e timestamp do último deploy."""
    import pathlib

    last_deploy: str | None = None
    try:
        ts_file = pathlib.Path("/app/.deploy_ts")
        if ts_file.exists():
            last_deploy = ts_file.read_text().strip()
    except Exception:
        pass
    return {
        "version": __version__,
        "build_sha": settings.BUILD_SHA,
        "environment": settings.ENVIRONMENT,
        "deployed_at": last_deploy,
    }


# ── /admin/metrics ─────────────────────────────────────────────────────────────


@router.get("/metrics", dependencies=[Depends(_require_admin)])
async def get_metrics(db: AsyncSession = Depends(get_db)) -> dict:
    """KPIs completos para o ProductionDashboard — atualiza a cada 30s."""

    now = datetime.now(timezone.utc)

    # Janelas de tempo
    t1h = now - timedelta(hours=1)
    t24h = now - timedelta(hours=24)
    t7d = now - timedelta(days=7)
    t14d = now - timedelta(days=14)
    t30d = now - timedelta(days=30)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Todos os resultados em paralelo
    (
        sys_metrics,
        user_metrics,
        product_metrics,
        cost_metrics,
    ) = await asyncio.gather(
        _system_metrics(db, now, t1h, t24h, t7d, t30d),
        _user_metrics(db, now, t24h, t7d, t14d),
        _product_metrics(db, now, t24h, t7d),
        _cost_metrics(db, now, month_start, t30d),
    )

    return {
        "generated_at": now.isoformat(),
        "system": sys_metrics,
        "users": user_metrics,
        "product": product_metrics,
        "costs": cost_metrics,
    }


# ── Helpers de agregação ───────────────────────────────────────────────────────


async def _system_metrics(db, now, t1h, t24h, t7d, t30d) -> dict:
    from app.models.request_log import RequestLog

    async def _uptime_pct(since: datetime) -> float:
        total_q = await db.execute(
            select(func.count(RequestLog.id)).where(RequestLog.timestamp >= since)
        )
        total = total_q.scalar_one() or 0
        if total == 0:
            return 100.0
        err_q = await db.execute(
            select(func.count(RequestLog.id)).where(
                RequestLog.timestamp >= since, RequestLog.status_code >= 500
            )
        )
        errors = err_q.scalar_one() or 0
        return round((1 - errors / total) * 100, 2)

    async def _percentiles(since: datetime) -> dict:
        rows_q = await db.execute(
            select(RequestLog.duration_ms)
            .where(
                RequestLog.timestamp >= since,
                RequestLog.status_code < 500,
            )
            .order_by(RequestLog.duration_ms)
        )
        durations = [r[0] for r in rows_q.all()]
        if not durations:
            return {"p50": 0, "p95": 0, "p99": 0}

        def pct(data, p):
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        return {
            "p50": pct(durations, 50),
            "p95": pct(durations, 95),
            "p99": pct(durations, 99),
        }

    uptime_24h, uptime_7d, uptime_30d, error_rate, latency = await asyncio.gather(
        _uptime_pct(t24h),
        _uptime_pct(t7d),
        _uptime_pct(t30d),
        _error_rate_1h(db, t1h),
        _percentiles(t1h),
    )

    # Celery queues via Redis
    queues = await _celery_queues()

    # WebSocket connections
    from app.ws_manager import manager

    ws_connections = len(manager.active)

    return {
        "uptime_24h_pct": uptime_24h,
        "uptime_7d_pct": uptime_7d,
        "uptime_30d_pct": uptime_30d,
        "error_rate_1h_pct": error_rate,
        "latency_ms": latency,
        "celery_queues": queues,
        "ws_connections": ws_connections,
    }


async def _error_rate_1h(db, t1h) -> float:
    from app.models.request_log import RequestLog

    total_q = await db.execute(select(func.count(RequestLog.id)).where(RequestLog.timestamp >= t1h))
    total = total_q.scalar_one() or 0
    if total == 0:
        return 0.0
    err_q = await db.execute(
        select(func.count(RequestLog.id)).where(
            RequestLog.timestamp >= t1h, RequestLog.status_code >= 500
        )
    )
    errors = err_q.scalar_one() or 0
    return round(errors / total * 100, 2)


async def _celery_queues() -> dict:
    try:
        from app.cache.redis_cache import _get_client

        client = _get_client()
        copy_len, art_len, research_len = await asyncio.gather(
            client.llen("copy"),
            client.llen("art"),
            client.llen("research"),
            return_exceptions=True,
        )
        return {
            "copy": copy_len if isinstance(copy_len, int) else 0,
            "art": art_len if isinstance(art_len, int) else 0,
            "research": research_len if isinstance(research_len, int) else 0,
        }
    except Exception:
        return {"copy": 0, "art": 0, "research": 0}


async def _user_metrics(db, now, t24h, t7d, t14d) -> dict:
    from app.models.user import User
    from app.models.pipeline import Pipeline

    # Totais
    total_q, deleted_q = await asyncio.gather(
        db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None))),
        db.execute(select(func.count(User.id)).where(User.deleted_at.isnot(None))),
    )
    total_users = total_q.scalar_one() or 0

    # Ativos: tiveram pipeline hoje / esta semana
    active_24h_q = await db.execute(
        select(func.count(func.distinct(Pipeline.user_id))).where(Pipeline.created_at >= t24h)
    )
    active_7d_q = await db.execute(
        select(func.count(func.distinct(Pipeline.user_id))).where(Pipeline.created_at >= t7d)
    )
    active_24h = active_24h_q.scalar_one() or 0
    active_7d = active_7d_q.scalar_one() or 0

    # Onboarding completion
    completed_q = await db.execute(
        select(func.count(User.id)).where(
            User.onboarding_completed.is_(True), User.deleted_at.is_(None)
        )
    )
    completed = completed_q.scalar_one() or 0
    onboarding_rate = round(completed / total_users * 100, 1) if total_users > 0 else 0.0

    # Novos cadastros últimos 14 dias (por dia)
    signups_q = await db.execute(
        select(
            func.date(User.created_at).label("day"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= t14d, User.deleted_at.is_(None))
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    signups_by_day = [{"day": str(day), "count": cnt} for day, cnt in signups_q.all()]

    return {
        "total": total_users,
        "active_today": active_24h,
        "active_this_week": active_7d,
        "onboarding_completion_pct": onboarding_rate,
        "signups_last_14d": signups_by_day,
    }


async def _product_metrics(db, now, t24h, t7d) -> dict:
    from app.models.pipeline import Pipeline, PipelineState
    from app.models.copy import Copy, CopyStatus

    # Pipelines
    async def _pipeline_counts(since):
        total_q = await db.execute(
            select(func.count(Pipeline.id)).where(Pipeline.created_at >= since)
        )
        pub_q = await db.execute(
            select(func.count(Pipeline.id)).where(
                Pipeline.created_at >= since,
                Pipeline.state == PipelineState.PUBLISHED,
            )
        )
        total = total_q.scalar_one() or 0
        published = pub_q.scalar_one() or 0
        return total, published

    (total_24h, pub_24h), (total_7d, pub_7d) = await asyncio.gather(
        _pipeline_counts(t24h),
        _pipeline_counts(t7d),
    )

    completion_rate = round(pub_7d / total_7d * 100, 1) if total_7d > 0 else 0.0

    # Copies por canal (últimos 7 dias)
    copies_by_channel_q = await db.execute(
        select(Copy.channel, func.count(Copy.id))
        .join(Pipeline, Copy.pipeline_id == Pipeline.id)
        .where(Pipeline.created_at >= t7d)
        .group_by(Copy.channel)
    )
    copies_by_channel = {ch: cnt for ch, cnt in copies_by_channel_q.all()}

    # Publicações por canal
    pubs_by_channel_q = await db.execute(
        select(Copy.channel, func.count(Copy.id))
        .join(Pipeline, Copy.pipeline_id == Pipeline.id)
        .where(
            Pipeline.created_at >= t7d,
            Copy.status == CopyStatus.PUBLISHED,
        )
        .group_by(Copy.channel)
    )
    pubs_by_channel = {ch: cnt for ch, cnt in pubs_by_channel_q.all()}

    # Tempo médio do pipeline (PUBLISHED) em minutos — últimos 7 dias
    # updated_at - created_at para pipelines PUBLISHED
    avg_time_q = await db.execute(
        select(Pipeline.created_at, Pipeline.updated_at).where(
            Pipeline.created_at >= t7d,
            Pipeline.state == PipelineState.PUBLISHED,
        )
    )
    times = [
        (row.updated_at - row.created_at).total_seconds() / 60
        for row in avg_time_q.all()
        if row.updated_at and row.created_at
    ]
    avg_pipeline_min = round(statistics.mean(times), 1) if times else None

    return {
        "pipelines_today": total_24h,
        "pipelines_this_week": total_7d,
        "published_today": pub_24h,
        "published_this_week": pub_7d,
        "completion_rate_pct": completion_rate,
        "copies_by_channel": copies_by_channel,
        "publications_by_channel": pubs_by_channel,
        "avg_pipeline_minutes": avg_pipeline_min,
    }


async def _cost_metrics(db, now, month_start, t30d) -> dict:
    from app.models.ai_usage import AiUsageLog

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_of_month = now.day

    async def _agg(since):
        q = await db.execute(
            select(
                func.sum(AiUsageLog.cost_usd).label("cost"),
                func.sum(AiUsageLog.tokens_in).label("t_in"),
                func.sum(AiUsageLog.tokens_out).label("t_out"),
                func.count(AiUsageLog.id).label("calls"),
            ).where(AiUsageLog.created_at >= since)
        )
        row = q.one()
        return {
            "cost_usd": round(float(row.cost or 0), 4),
            "tokens_in": int(row.t_in or 0),
            "tokens_out": int(row.t_out or 0),
            "calls": int(row.calls or 0),
        }

    today_data, month_data = await asyncio.gather(
        _agg(today_start),
        _agg(month_start),
    )

    # Projeção até fim do mês
    days_in_month = 30
    monthly_projection = (
        round(month_data["cost_usd"] / day_of_month * days_in_month, 2) if day_of_month > 0 else 0.0
    )

    # Tokens por agente (últimos 30 dias)
    agents_q = await db.execute(
        select(
            AiUsageLog.agent_name,
            func.sum(AiUsageLog.cost_usd).label("cost"),
            func.sum(AiUsageLog.tokens_in + AiUsageLog.tokens_out).label("tokens"),
            func.count(AiUsageLog.id).label("calls"),
        )
        .where(AiUsageLog.created_at >= t30d)
        .group_by(AiUsageLog.agent_name)
        .order_by(func.sum(AiUsageLog.cost_usd).desc())
    )
    by_agent = [
        {
            "agent": a,
            "cost_usd": round(float(c), 4),
            "tokens": int(t),
            "calls": int(n),
        }
        for a, c, t, n in agents_q.all()
    ]

    # Custo médio por publicação
    from app.models.pipeline import Pipeline, PipelineState

    pub_count_q = await db.execute(
        select(func.count(Pipeline.id)).where(
            Pipeline.created_at >= month_start,
            Pipeline.state == PipelineState.PUBLISHED,
        )
    )
    pub_count = pub_count_q.scalar_one() or 0
    cost_per_pub = round(month_data["cost_usd"] / pub_count, 4) if pub_count > 0 else None

    return {
        "today_usd": today_data["cost_usd"],
        "month_usd": month_data["cost_usd"],
        "month_projection_usd": monthly_projection,
        "alert_threshold_usd": settings.AI_COST_ALERT_USD,
        "cost_per_publication": cost_per_pub,
        "by_agent": by_agent,
    }

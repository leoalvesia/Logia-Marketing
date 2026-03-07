"""Tasks Celery de alertas de negócio.

Schedules (via Celery Beat):
  business_health_check — a cada hora
  weekly_business_report — segunda-feira às 8h UTC

Alertas:
  - 0 pipelines em 24h → "Plataforma sem uso"
  - Taxa de conclusão < 30% → "Muitos pipelines abandonados"
  - Error rate publicação > 10% por canal → alerta crítico
  - Relatório semanal comparativo (semana atual vs anterior)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


def _slack(text: str) -> None:
    if not settings.SLACK_WEBHOOK:
        return
    try:
        httpx.post(settings.SLACK_WEBHOOK, json={"text": text}, timeout=5).raise_for_status()
    except Exception as exc:
        logger.error("slack_post_failed: %s", exc)


def _run(coro):
    return asyncio.run(coro)


async def _pipeline_stats(since: datetime, db) -> dict:
    from sqlalchemy import func, select
    from app.models.pipeline import Pipeline, PipelineState
    from app.models.copy import Copy, CopyStatus

    total_q = await db.execute(
        select(func.count(Pipeline.id)).where(Pipeline.created_at >= since)
    )
    total = total_q.scalar_one() or 0

    published_q = await db.execute(
        select(func.count(Pipeline.id)).where(
            Pipeline.created_at >= since,
            Pipeline.state == PipelineState.PUBLISHED,
        )
    )
    published = published_q.scalar_one() or 0

    # Error rate por canal: copies FAILED / total copies no período
    channel_q = await db.execute(
        select(Copy.channel, func.count(Copy.id))
        .join(Pipeline, Copy.pipeline_id == Pipeline.id)
        .where(Pipeline.created_at >= since)
        .group_by(Copy.channel)
    )
    channel_total = {ch: cnt for ch, cnt in channel_q.all()}

    failed_pub_q = await db.execute(
        select(Copy.channel, func.count(Copy.id))
        .join(Pipeline, Copy.pipeline_id == Pipeline.id)
        .where(
            Pipeline.created_at >= since,
            Copy.status == CopyStatus.DELETED,  # proxy para falha de publicação
        )
        .group_by(Copy.channel)
    )
    channel_failed = {ch: cnt for ch, cnt in failed_pub_q.all()}

    return {
        "total": total,
        "published": published,
        "completion_rate": round(published / total * 100, 1) if total > 0 else 0.0,
        "channel_total": channel_total,
        "channel_failed": channel_failed,
    }


@celery_app.task(name="app.tasks.business_alerts.business_health_check")
def business_health_check() -> None:
    """Roda a cada hora — verifica métricas de negócio e alerta se necessário."""

    async def _check() -> None:
        from app.database import AsyncSessionLocal

        now = datetime.now(timezone.utc)
        since_24h = now - timedelta(hours=24)

        async with AsyncSessionLocal() as db:
            stats = await _pipeline_stats(since_24h, db)

        alerts = []

        # Alerta 1: Plataforma sem uso (0 pipelines em 24h)
        if stats["total"] == 0:
            alerts.append(
                "🚨 *Plataforma sem uso*\n"
                "Nenhum pipeline iniciado nas últimas 24h.\n"
                "Verificar: email de reativação, status do servidor."
            )

        # Alerta 2: Taxa de conclusão < 30%
        if stats["total"] >= 5 and stats["completion_rate"] < 30.0:
            alerts.append(
                f"⚠️ *Muitos pipelines abandonados*\n"
                f"Taxa de conclusão: *{stats['completion_rate']}%* "
                f"({stats['published']}/{stats['total']} nas últimas 24h)\n"
                f"Meta: > 30%"
            )

        # Alerta 3: Error rate > 10% por canal
        for channel, total in stats["channel_total"].items():
            failed = stats["channel_failed"].get(channel, 0)
            if total >= 5 and failed / total > 0.10:
                rate = round(failed / total * 100, 1)
                alerts.append(
                    f"🔴 *Error rate crítico — {channel}*\n"
                    f"Falhas: *{rate}%* ({failed}/{total})\n"
                    f"Verificar token e permissões da plataforma."
                )

        for alert in alerts:
            _slack(alert)
            logger.warning("business_alert_sent", alert=alert[:100])

        if not alerts:
            logger.info("business_health_check_ok", stats=stats)

    _run(_check())


@celery_app.task(name="app.tasks.business_alerts.weekly_business_report")
def weekly_business_report() -> None:
    """Roda toda segunda às 8h UTC — relatório comparativo semana atual vs anterior."""

    async def _report() -> None:
        from app.database import AsyncSessionLocal
        from sqlalchemy import func, select
        from app.models.user import User

        now = datetime.now(timezone.utc)
        this_week_start = now - timedelta(days=7)
        last_week_start = now - timedelta(days=14)

        async with AsyncSessionLocal() as db:
            stats_this = await _pipeline_stats(this_week_start, db)
            stats_last = await _pipeline_stats(last_week_start, db)

            # Novos usuários
            new_users_q = await db.execute(
                select(func.count(User.id)).where(
                    User.created_at >= this_week_start,
                    User.deleted_at.is_(None),
                )
            )
            new_users = new_users_q.scalar_one() or 0

            new_users_prev_q = await db.execute(
                select(func.count(User.id)).where(
                    User.created_at >= last_week_start,
                    User.created_at < this_week_start,
                    User.deleted_at.is_(None),
                )
            )
            new_users_prev = new_users_prev_q.scalar_one() or 0

        def _delta(curr: float, prev: float) -> str:
            if prev == 0:
                return "(novo)" if curr > 0 else ""
            pct = round((curr - prev) / prev * 100, 1)
            return f"({'↑' if pct >= 0 else '↓'}{abs(pct)}%)"

        text = (
            f"📊 *Relatório Semanal Logia*\n"
            f"Semana: {this_week_start.strftime('%d/%m')} – {now.strftime('%d/%m/%Y')}\n\n"
            f"*Usuários novos:* {new_users} {_delta(new_users, new_users_prev)}\n"
            f"*Pipelines iniciados:* {stats_this['total']} {_delta(stats_this['total'], stats_last['total'])}\n"
            f"*Publicações:* {stats_this['published']} {_delta(stats_this['published'], stats_last['published'])}\n"
            f"*Taxa de conclusão:* {stats_this['completion_rate']}% "
            f"{_delta(stats_this['completion_rate'], stats_last['completion_rate'])}\n\n"
            f"Dashboard: https://app.logia.com.br/admin"
        )
        _slack(text)
        logger.info("weekly_report_sent", stats=stats_this)

    _run(_report())

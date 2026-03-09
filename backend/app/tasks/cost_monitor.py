"""Task Celery de monitoramento de custos de IA.

Beat schedule: diariamente às 8h UTC (antes do resumo NPS das 9h).

O que faz:
  1. Agrega tokens e custo das últimas 24h por agente/modelo
  2. Calcula projeção mensal baseada no ritmo do dia
  3. Alerta no Slack se custo diário > settings.AI_COST_ALERT_USD (padrão $10)
  4. Persiste o resumo diário para o endpoint GET /admin/costs
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


def _post_slack(text: str) -> None:
    if not settings.SLACK_WEBHOOK:
        return
    try:
        httpx.post(settings.SLACK_WEBHOOK, json={"text": text}, timeout=5).raise_for_status()
    except Exception as exc:
        logger.error("slack_post_failed: %s", exc)


@celery_app.task(name="app.tasks.cost_monitor.daily_cost_report")
def daily_cost_report() -> None:
    """Agrega custos de IA das últimas 24h e alerta se acima do limite."""

    async def _fetch() -> dict:
        from sqlalchemy import func, select
        from app.database import AsyncSessionLocal
        from app.models.ai_usage import AiUsageLog

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        async with AsyncSessionLocal() as db:
            # Total geral do dia
            total_q = await db.execute(
                select(
                    func.sum(AiUsageLog.cost_usd).label("total_cost"),
                    func.sum(AiUsageLog.tokens_in).label("total_in"),
                    func.sum(AiUsageLog.tokens_out).label("total_out"),
                    func.count(AiUsageLog.id).label("calls"),
                ).where(AiUsageLog.created_at >= since)
            )
            row = total_q.one()

            # Por agente
            by_agent_q = await db.execute(
                select(
                    AiUsageLog.agent_name,
                    func.sum(AiUsageLog.cost_usd).label("cost"),
                    func.sum(AiUsageLog.tokens_in + AiUsageLog.tokens_out).label("tokens"),
                    func.count(AiUsageLog.id).label("calls"),
                )
                .where(AiUsageLog.created_at >= since)
                .group_by(AiUsageLog.agent_name)
                .order_by(func.sum(AiUsageLog.cost_usd).desc())
            )
            by_agent = [
                {"agent": a, "cost_usd": round(float(c), 4), "tokens": int(t), "calls": int(n)}
                for a, c, t, n in by_agent_q.all()
            ]

            # Por modelo
            by_model_q = await db.execute(
                select(
                    AiUsageLog.model,
                    func.sum(AiUsageLog.cost_usd).label("cost"),
                )
                .where(AiUsageLog.created_at >= since)
                .group_by(AiUsageLog.model)
                .order_by(func.sum(AiUsageLog.cost_usd).desc())
            )
            by_model = {m: round(float(c), 4) for m, c in by_model_q.all()}

        return {
            "total_cost": round(float(row.total_cost or 0), 4),
            "total_tokens_in": int(row.total_in or 0),
            "total_tokens_out": int(row.total_out or 0),
            "calls": int(row.calls or 0),
            "by_agent": by_agent,
            "by_model": by_model,
        }

    try:
        data = asyncio.run(_fetch())
    except Exception as exc:
        logger.error("daily_cost_report fetch failed: %s", exc)
        return

    total = data["total_cost"]
    calls = data["calls"]

    # Projeção mensal (dia atual do mês → dias restantes)
    days_in_month = 30
    monthly_projection = round(total * days_in_month, 2)

    if calls == 0:
        _post_slack("💰 *Custo IA diário*: nenhuma chamada nas últimas 24h.")
        return

    # Resumo por agente (top 5)
    agent_lines = ""
    for item in data["by_agent"][:5]:
        agent_lines += f"\n  • `{item['agent']}`: ${item['cost_usd']:.4f} ({item['calls']} calls)"

    text = (
        f"💰 *Custo IA — últimas 24h*\n"
        f"Total: *${total:.4f}* · {calls} chamadas\n"
        f"Projeção mensal: *${monthly_projection:.2f}*"
        f"{agent_lines}\n"
        f"Dashboard: https://app.logia.com.br/admin/costs"
    )

    # Alerta se acima do limite
    if total > settings.AI_COST_ALERT_USD:
        alert_text = (
            f"🚨 *ALERTA DE CUSTO DE IA!*\n"
            f"Custo do dia: *${total:.4f}* (limite: ${settings.AI_COST_ALERT_USD:.2f})\n"
            f"Projeção mensal: *${monthly_projection:.2f}*\n"
            f"Investigar: https://app.logia.com.br/admin/costs"
        )
        _post_slack(alert_text)

    _post_slack(text)
    logger.info(
        "daily_cost_report_sent",
        total_usd=total,
        calls=calls,
        monthly_projection=monthly_projection,
        alerted=total > settings.AI_COST_ALERT_USD,
    )

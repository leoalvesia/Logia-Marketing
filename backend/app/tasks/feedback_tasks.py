"""Tarefas Celery para alertas de feedback.

Tasks:
  alert_low_nps      — NPS ≤ 6 → Slack imediato
  alert_bug_report   — Bug report → Slack imediato
  daily_nps_summary  — Resumo diário às 9h (agendado via beat)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _post_slack(text: str) -> bool:
    """Envia mensagem ao Slack via Incoming Webhook. Retorna True se enviou."""
    if not settings.SLACK_WEBHOOK:
        logger.info("slack_skipped: SLACK_WEBHOOK não configurado")
        return False
    try:
        resp = httpx.post(
            settings.SLACK_WEBHOOK,
            json={"text": text},
            timeout=5,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("slack_post_failed: %s", exc)
        return False


# ── Tasks ──────────────────────────────────────────────────────────────────────


@celery_app.task(name="app.tasks.feedback_tasks.alert_low_nps", max_retries=2)
def alert_low_nps(user_id: str, user_email: str, score: int, comment: str | None) -> None:
    """Alerta imediato no Slack quando NPS ≤ 6 (detrator)."""
    emoji = "🔴" if score <= 4 else "🟡"
    comment_text = f"\n> _{comment}_" if comment else ""
    text = (
        f"{emoji} *NPS detrator recebido!*\n"
        f"Usuário: `{user_email}`\n"
        f"Nota: *{score}/10*{comment_text}\n"
        f"Dashboard: https://app.logia.com.br/admin/feedback"
    )
    _post_slack(text)


@celery_app.task(name="app.tasks.feedback_tasks.alert_bug_report", max_retries=2)
def alert_bug_report(
    bug_id: str,
    user_email: str,
    description: str,
    url: str | None,
) -> None:
    """Alerta imediato no Slack quando um bug report é criado."""
    url_text = f"\nURL: `{url}`" if url else ""
    text = (
        f"🐛 *Novo bug report!*\n"
        f"Usuário: `{user_email}`{url_text}\n"
        f"Descrição: {description[:200]}\n"
        f"Dashboard: https://app.logia.com.br/admin/feedback"
    )
    _post_slack(text)


@celery_app.task(name="app.tasks.feedback_tasks.daily_nps_summary")
def daily_nps_summary() -> None:
    """Envia resumo diário de NPS às 9h com score médio e novos comentários."""
    import asyncio

    async def _fetch_stats():
        from sqlalchemy import func, select
        from app.database import AsyncSessionLocal
        from app.models.feedback import NpsFeedback

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(
                    func.avg(NpsFeedback.score).label("avg"),
                    func.count(NpsFeedback.id).label("total"),
                ).where(NpsFeedback.created_at >= since)
            )
            row = result.one()
            avg_score = round(float(row.avg), 1) if row.avg else None
            total = row.total

            # Comentários recentes (últimas 24h)
            comments_q = await db.execute(
                select(NpsFeedback.score, NpsFeedback.comment)
                .where(NpsFeedback.created_at >= since)
                .where(NpsFeedback.comment.isnot(None))
                .limit(5)
            )
            comments = comments_q.all()
        return avg_score, total, comments

    try:
        avg, total, comments = asyncio.run(_fetch_stats())
    except Exception as exc:
        logger.error("daily_nps_summary fetch failed: %s", exc)
        return

    if total == 0:
        _post_slack("📊 *NPS diário*: nenhuma resposta nas últimas 24h.")
        return

    comment_lines = ""
    for score, comment in comments:
        emoji = "🟢" if score >= 9 else ("🟡" if score >= 7 else "🔴")
        comment_lines += f"\n{emoji} [{score}/10] _{comment[:100]}_"

    text = (
        f"📊 *Resumo NPS — últimas 24h*\n"
        f"Média: *{avg}/10* · {total} resposta(s)"
        f"{comment_lines}\n"
        f"Dashboard: https://app.logia.com.br/admin/feedback"
    )
    _post_slack(text)

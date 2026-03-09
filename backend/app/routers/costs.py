"""Endpoints de monitoramento de custos de IA.

Admin only (X-Admin-Key):
  GET /admin/costs          → resumo dos últimos N dias por dia e por agente
  GET /admin/costs/live     → custo acumulado do dia atual (tempo real)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.ai_usage import AiUsageLog

router = APIRouter()


# ── Admin dependency ───────────────────────────────────────────────────────────


async def _require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if not settings.ADMIN_KEY:
        raise HTTPException(status_code=503, detail="ADMIN_KEY não configurado")
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("", dependencies=[Depends(_require_admin)])
async def get_cost_history(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Histórico de custo de IA agrupado por dia e por agente."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Totais do período
    totals_q = await db.execute(
        select(
            func.sum(AiUsageLog.cost_usd).label("total_cost"),
            func.sum(AiUsageLog.tokens_in).label("total_in"),
            func.sum(AiUsageLog.tokens_out).label("total_out"),
            func.count(AiUsageLog.id).label("calls"),
        ).where(AiUsageLog.created_at >= since)
    )
    row = totals_q.one()
    total_cost = round(float(row.total_cost or 0), 4)
    calls = int(row.calls or 0)

    # Projeção mensal baseada na média diária do período
    avg_daily = total_cost / days if days > 0 else 0
    monthly_projection = round(avg_daily * 30, 2)

    # Por dia (últimos N dias)
    by_day_q = await db.execute(
        select(
            func.date(AiUsageLog.created_at).label("day"),
            func.sum(AiUsageLog.cost_usd).label("cost"),
            func.count(AiUsageLog.id).label("calls"),
            func.sum(AiUsageLog.tokens_in + AiUsageLog.tokens_out).label("tokens"),
        )
        .where(AiUsageLog.created_at >= since)
        .group_by(func.date(AiUsageLog.created_at))
        .order_by(func.date(AiUsageLog.created_at))
    )
    by_day = [
        {
            "day": str(day),
            "cost_usd": round(float(cost), 4),
            "calls": int(n),
            "tokens": int(t),
        }
        for day, cost, n, t in by_day_q.all()
    ]

    # Por agente (período completo)
    by_agent_q = await db.execute(
        select(
            AiUsageLog.agent_name,
            func.sum(AiUsageLog.cost_usd).label("cost"),
            func.sum(AiUsageLog.tokens_in).label("tokens_in"),
            func.sum(AiUsageLog.tokens_out).label("tokens_out"),
            func.count(AiUsageLog.id).label("calls"),
        )
        .where(AiUsageLog.created_at >= since)
        .group_by(AiUsageLog.agent_name)
        .order_by(func.sum(AiUsageLog.cost_usd).desc())
    )
    by_agent = [
        {
            "agent": a,
            "cost_usd": round(float(c), 4),
            "tokens_in": int(ti),
            "tokens_out": int(to),
            "calls": int(n),
        }
        for a, c, ti, to, n in by_agent_q.all()
    ]

    # Por modelo
    by_model_q = await db.execute(
        select(
            AiUsageLog.model,
            func.sum(AiUsageLog.cost_usd).label("cost"),
            func.count(AiUsageLog.id).label("calls"),
        )
        .where(AiUsageLog.created_at >= since)
        .group_by(AiUsageLog.model)
        .order_by(func.sum(AiUsageLog.cost_usd).desc())
    )
    by_model = [
        {"model": m, "cost_usd": round(float(c), 4), "calls": int(n)}
        for m, c, n in by_model_q.all()
    ]

    return {
        "period_days": days,
        "total_cost_usd": total_cost,
        "total_calls": calls,
        "avg_daily_usd": round(avg_daily, 4),
        "monthly_projection_usd": monthly_projection,
        "alert_threshold_usd": settings.AI_COST_ALERT_USD,
        "by_day": by_day,
        "by_agent": by_agent,
        "by_model": by_model,
    }


@router.get("/live", dependencies=[Depends(_require_admin)])
async def get_cost_today(db: AsyncSession = Depends(get_db)) -> dict:
    """Custo acumulado do dia atual (desde meia-noite UTC)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    q = await db.execute(
        select(
            func.sum(AiUsageLog.cost_usd).label("cost"),
            func.sum(AiUsageLog.tokens_in).label("tokens_in"),
            func.sum(AiUsageLog.tokens_out).label("tokens_out"),
            func.count(AiUsageLog.id).label("calls"),
        ).where(AiUsageLog.created_at >= today_start)
    )
    row = q.one()
    cost = round(float(row.cost or 0), 4)

    return {
        "date": today_start.date().isoformat(),
        "cost_usd": cost,
        "tokens_in": int(row.tokens_in or 0),
        "tokens_out": int(row.tokens_out or 0),
        "calls": int(row.calls or 0),
        "alert_threshold_usd": settings.AI_COST_ALERT_USD,
        "above_threshold": cost > settings.AI_COST_ALERT_USD,
    }

"""Helper para registrar uso de tokens de IA no banco.

Uso nos agentes de copy/art:
    from app.ai_logger import log_ai_usage, estimate_cost

    cost = estimate_cost("claude-sonnet-4-6", tokens_in=1200, tokens_out=350)
    await log_ai_usage(db, agent="copy_instagram", model="claude-sonnet-4-6",
                       tokens_in=1200, tokens_out=350, pipeline_id=session_id)

Precos atualizados em 2026-03 — revisar trimestralmente.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import get_logger

logger = get_logger(__name__)

# ── Preços por 1M de tokens (USD) ─────────────────────────────────────────────
# Fonte: precos oficiais Anthropic e OpenAI (2026-03)
_PRICES: dict[str, tuple[float, float]] = {
    # modelo: (preco_in_por_1M, preco_out_por_1M)
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (0.25, 1.25),
    # fallback — prefixo
    "claude-opus": (15.00, 75.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-haiku": (0.25, 1.25),
    # OpenAI
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Calcula custo estimado em USD para uma chamada de LLM."""
    prices = _PRICES.get(model)
    if not prices:
        # Fallback por prefixo
        for key, val in _PRICES.items():
            if model.startswith(key):
                prices = val
                break
        else:
            logger.warning("ai_cost_unknown_model", model=model)
            return 0.0

    price_in, price_out = prices
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


async def log_ai_usage(
    db: AsyncSession,
    *,
    agent: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    pipeline_id: str | None = None,
) -> float:
    """Persiste um registro de uso de IA. Retorna o custo calculado em USD.

    Silencioso em caso de falha — nunca deixar o agente falhar por causa do log.
    """
    from app.models.ai_usage import AiUsageLog

    cost = estimate_cost(model, tokens_in, tokens_out)
    try:
        entry = AiUsageLog(
            id=str(uuid.uuid4()),
            agent_name=agent,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            pipeline_id=pipeline_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        await db.flush()  # não commita — deixa a transação do caller decidir
        logger.debug(
            "ai_usage_logged",
            agent=agent,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(cost, 6),
        )
    except Exception as exc:
        logger.warning("ai_usage_log_failed", error=str(exc))

    return cost

"""Model para rastreamento de uso de tokens de IA por agente."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AiUsageLog(Base):
    """Registra cada chamada de LLM com tokens consumidos e custo estimado.

    Como usar nos agentes:
        from app.models.ai_usage import log_ai_usage
        await log_ai_usage(db, agent="copy_instagram", model="claude-sonnet-4-6",
                           tokens_in=1200, tokens_out=350)
    """

    __tablename__ = "ai_usage_logs"
    __table_args__ = (
        # Queries mais comuns: por dia e por agente
        Index("ix_ai_usage_created", "created_at"),
        Index("ix_ai_usage_agent_created", "agent_name", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Nome do agente: copy_instagram, copy_linkedin, copy_twitter,
    #                 copy_youtube, copy_email, art_generator,
    #                 research_youtube, research_instagram, etc.
    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    # Modelo exato: claude-sonnet-4-6, claude-opus-4-6, gpt-4o, gpt-4o-mini
    model: Mapped[str] = mapped_column(String(100))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    # Custo já calculado em USD (evita recalcular com preços desatualizados)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    # pipeline_id opcional para rastrear custo por sessão
    pipeline_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<AiUsageLog agent={self.agent_name!r} model={self.model!r} "
            f"cost=${self.cost_usd:.4f}>"
        )

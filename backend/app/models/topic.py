"""Model de sugestão de tema gerada pelo Orquestrador de Pesquisa."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Topic(Base):
    """
    Cada registro representa uma sugestão de tema dentro de um pipeline.
    O Orquestrador gera até 10 por execução (rank 1–10).

    Regra crítica: source_url NUNCA pode ser vazio — todo tema tem fonte verificável.
    """

    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)

    # Obrigatório — regra: nunca inventar. Todo dado tem fonte.
    source_url: Mapped[str] = mapped_column(Text)

    # JSON array: ["instagram", "youtube", "linkedin", "twitter"]
    channels_found: Mapped[str] = mapped_column(Text, default="[]")

    # Score = frequência×0.4 + recência×0.35 + relevância ao nicho×0.25
    score: Mapped[float] = mapped_column(Float, default=0.0)

    # Posição no ranking (1 = mais relevante, 10 = menos relevante)
    rank: Mapped[int] = mapped_column(Integer)

    # Quando o conteúdo original foi publicado na fonte
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    def __repr__(self) -> str:
        return f"<Topic rank={self.rank} score={self.score:.2f} title={self.title[:40]!r}>"

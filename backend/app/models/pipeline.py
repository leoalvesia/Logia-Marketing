"""Model do pipeline de conteúdo — tabela pipeline_sessions."""

from __future__ import annotations
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Index, String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineState(str, enum.Enum):
    """Os 11 estados do pipeline conforme PRD seção 4."""

    RESEARCHING = "RESEARCHING"
    ORCHESTRATING = "ORCHESTRATING"
    AWAITING_SELECTION = "AWAITING_SELECTION"
    GENERATING_COPY = "GENERATING_COPY"
    COPY_REVIEW = "COPY_REVIEW"
    GENERATING_ART = "GENERATING_ART"
    ART_REVIEW = "ART_REVIEW"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class Pipeline(Base):
    __tablename__ = "pipeline_sessions"
    __table_args__ = (Index("ix_pipeline_sessions_user_state", "user_id", "state"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    state: Mapped[PipelineState] = mapped_column(
        SAEnum(PipelineState), default=PipelineState.RESEARCHING
    )

    # ID do topic escolhido pelo usuário após a pesquisa.
    # Sem FK para evitar dependência circular com a tabela topics.
    topic_selected: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # JSON array dos canais selecionados: ["instagram", "linkedin"]
    channels_selected: Mapped[str] = mapped_column(Text, default="[]")

    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    def __repr__(self) -> str:
        return f"<Pipeline id={self.id!r} state={self.state!r}>"

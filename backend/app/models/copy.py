"""Model de copy gerada pelos agentes."""

from __future__ import annotations
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Index, String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CopyChannel(str, enum.Enum):
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    EMAIL = "email"


class CopyStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    DELETED = "deleted"


class Copy(Base):
    __tablename__ = "copies"
    __table_args__ = (
        Index("ix_copies_pipeline_channel_status", "pipeline_id", "channel", "status"),
        Index("ix_copies_created_at_desc", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_sessions.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[CopyChannel] = mapped_column(SAEnum(CopyChannel))
    status: Mapped[CopyStatus] = mapped_column(SAEnum(CopyStatus), default=CopyStatus.DRAFT)

    # Conteúdo serializado em JSON — estrutura varia por canal:
    # Instagram: {"caption": "...", "hashtags": "...", "visual_hook": "..."}
    # Twitter:   {"tweets": ["...", "..."]}
    # LinkedIn:  {"text": "..."}
    # YouTube:   {"script": "...", "description": "...", "tags": "..."}
    # Email:     {"subject": "...", "intro": "...", "body": "...", "cta": "..."}
    content: Mapped[str] = mapped_column(Text)

    # Obrigatório — regra: nunca inventar. Todo dado tem fonte verificável.
    source_url: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    def __repr__(self) -> str:
        return f"<Copy id={self.id!r} channel={self.channel!r} status={self.status!r}>"

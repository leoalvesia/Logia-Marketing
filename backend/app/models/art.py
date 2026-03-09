"""Model de arte gerada pelos agentes."""

from __future__ import annotations
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Index, String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ArtType(str, enum.Enum):
    STATIC = "static"  # 1080×1080 ou 1080×1920
    CAROUSEL = "carousel"  # sequência de slides
    THUMBNAIL = "thumbnail"  # 1280×720


class Art(Base):
    __tablename__ = "arts"
    __table_args__ = (Index("ix_arts_pipeline_type", "pipeline_id", "type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    copy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("copies.id", ondelete="CASCADE"), index=True
    )
    pipeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_sessions.id", ondelete="CASCADE"), index=True
    )

    # Coluna DB: "type" — Python attribute: art_type (evita conflito com
    # o atributo especial __mapper_args__ do SQLAlchemy)
    art_type: Mapped[ArtType] = mapped_column("type", SAEnum(ArtType))

    # JSON array de URLs públicas das imagens geradas.
    # Estático:  ["https://drive.google.com/uc?id=..."]
    # Carrossel: ["slide1.png", "slide2.png", ...]
    # Thumbnail: ["v1.png", "v2.png", "v3.png"]  (2–3 variações)
    image_urls: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    def __repr__(self) -> str:
        return f"<Art id={self.id!r} type={self.art_type!r}>"

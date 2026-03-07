"""Model de perfis monitorados para pesquisa de tendências."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Index, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MonitoredProfile(Base):
    __tablename__ = "monitored_profiles"
    __table_args__ = (
        Index("ix_monitored_profiles_user_platform_active", "user_id", "platform", "active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Plataforma: "instagram" | "youtube" | "linkedin" | "twitter"
    platform: Mapped[str] = mapped_column(String(30))

    # @handle ou nome do canal/perfil
    handle: Mapped[str] = mapped_column(String(255))

    # URL completa do perfil (ex: https://instagram.com/logia)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    def __repr__(self) -> str:
        return f"<MonitoredProfile platform={self.platform!r} handle={self.handle!r}>"

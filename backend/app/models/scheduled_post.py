"""Model de post agendado para publicação."""

from __future__ import annotations
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ScheduledPostStatus(str, enum.Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_sessions.id", ondelete="CASCADE"), index=True
    )
    copy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("copies.id", ondelete="CASCADE"), index=True
    )
    art_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("arts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Canal de destino — mesmo enum de Copy
    channel: Mapped[str] = mapped_column(String(20))

    status: Mapped[ScheduledPostStatus] = mapped_column(
        SAEnum(ScheduledPostStatus), default=ScheduledPostStatus.PENDING
    )

    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    def __repr__(self) -> str:
        return (
            f"<ScheduledPost id={self.id!r} channel={self.channel!r}"
            f" status={self.status!r} for={self.scheduled_for}>"
        )

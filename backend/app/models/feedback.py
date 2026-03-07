"""Models de feedback: NPS, avaliação pós-publicação e bug reports."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class NpsFeedback(Base):
    __tablename__ = "nps_feedback"
    __table_args__ = (
        Index("ix_nps_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer)          # 0–10
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<NpsFeedback user={self.user_id!r} score={self.score}>"


class PostFeedback(Base):
    __tablename__ = "post_feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pipeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pipeline_sessions.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)         # 1–5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<PostFeedback pipeline={self.pipeline_id!r} rating={self.rating}>"


class BugReport(Base):
    __tablename__ = "bug_reports"
    __table_args__ = (
        Index("ix_bug_reports_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Base64 da screenshot (pode ser grande — guardado apenas se enviado)
    screenshot_b64: Mapped[str | None] = mapped_column(Text, nullable=True)
    # new | analyzing | resolved
    status: Mapped[str] = mapped_column(String(50), default="new")
    sentry_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<BugReport id={self.id!r} status={self.status!r}>"

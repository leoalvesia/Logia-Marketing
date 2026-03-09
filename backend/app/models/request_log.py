"""Model para logs de métricas de requisições HTTP."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RequestLog(Base):
    __tablename__ = "request_logs"
    __table_args__ = (Index("ix_request_logs_endpoint_timestamp", "endpoint", "timestamp"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10))
    duration_ms: Mapped[int] = mapped_column(Integer)
    status_code: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_now)

    def __repr__(self) -> str:
        return (
            f"<RequestLog {self.method} {self.endpoint} "
            f"{self.duration_ms}ms status={self.status_code}>"
        )

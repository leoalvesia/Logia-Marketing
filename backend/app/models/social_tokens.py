"""Model para tokens OAuth das redes sociais."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SocialToken(Base):
    """
    Armazena tokens OAuth por plataforma por usuário.
    Constraint única: um usuário tem no máximo 1 token ativo por plataforma.

    Os campos access_token e refresh_token são criptografados com Fernet
    antes de persistir. Use os métodos get/set para acessar os valores.
    Nunca acesse os campos crus em código de produção.
    """

    __tablename__ = "social_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_social_tokens_user_platform"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Plataforma: "instagram" | "twitter" | "linkedin" | "youtube"
    platform: Mapped[str] = mapped_column(String(30))

    # Armazenamento criptografado — usar set_access_token / get_access_token
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    # ── Métodos de acesso criptografado ───────────────────────────────────────

    def set_access_token(self, plain: str) -> None:
        """Criptografa e armazena o access token. Nunca passar o valor cru."""
        from app.crypto import encrypt_token
        self.access_token = encrypt_token(plain)

    def get_access_token(self) -> str:
        """Decriptografa e retorna o access token. Nunca logar o retorno."""
        from app.crypto import decrypt_token
        return decrypt_token(self.access_token)

    def set_refresh_token(self, plain: str | None) -> None:
        """Criptografa e armazena o refresh token."""
        if plain is None:
            self.refresh_token = None
            return
        from app.crypto import encrypt_token
        self.refresh_token = encrypt_token(plain)

    def get_refresh_token(self) -> str | None:
        """Decriptografa e retorna o refresh token."""
        if self.refresh_token is None:
            return None
        from app.crypto import decrypt_token
        return decrypt_token(self.refresh_token)

    def __repr__(self) -> str:
        # Nunca incluir tokens no repr — mesmo em debug
        return f"<SocialToken user={self.user_id!r} platform={self.platform!r}>"

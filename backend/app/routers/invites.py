"""Router de administração: convites de beta launch e feature flags.

Todos os endpoints exigem o header X-Admin-Key.
Se ADMIN_KEY não estiver configurado, os endpoints retornam 503.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.features import get_flags, set_flag
from app.models.invite import Invite

router = APIRouter()


# ── Admin auth dependency ──────────────────────────────────────────────────────


async def _require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if not settings.ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_KEY não configurado nesta instância",
        )
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")


# ── Schemas ────────────────────────────────────────────────────────────────────


class CreateInviteRequest(BaseModel):
    created_by: str = "admin"
    max_uses: int = Field(default=1, ge=1, le=100)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class InviteResponse(BaseModel):
    id: str
    code: str
    created_by: str
    used_by: Optional[str]
    used_at: Optional[datetime]
    uses_count: int
    max_uses: int
    expires_at: Optional[datetime]
    created_at: datetime
    status: str  # "available" | "used" | "expired"

    @classmethod
    def from_orm(cls, invite: Invite) -> "InviteResponse":
        if invite.is_expired:
            invite_status = "expired"
        elif invite.is_used:
            invite_status = "used"
        else:
            invite_status = "available"
        return cls(
            id=invite.id,
            code=invite.code,
            created_by=invite.created_by,
            used_by=invite.used_by,
            used_at=invite.used_at,
            uses_count=invite.uses_count,
            max_uses=invite.max_uses,
            expires_at=invite.expires_at,
            created_at=invite.created_at,
            status=invite_status,
        )


class FeatureFlagPatch(BaseModel):
    enabled: bool


# ── Convites ───────────────────────────────────────────────────────────────────


@router.post(
    "/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_require_admin)],
)
async def create_invite(
    body: CreateInviteRequest,
    db: AsyncSession = Depends(get_db),
) -> InviteResponse:
    """Gera um novo código de convite para beta."""
    expires_at: Optional[datetime] = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    invite = Invite(
        id=str(uuid.uuid4()),
        code=str(uuid.uuid4()),
        created_by=body.created_by,
        max_uses=body.max_uses,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return InviteResponse.from_orm(invite)


@router.get(
    "/invites",
    dependencies=[Depends(_require_admin)],
)
async def list_invites(db: AsyncSession = Depends(get_db)) -> dict:
    """Lista todos os convites com status (disponível / usado / expirado)."""
    result = await db.execute(select(Invite).order_by(Invite.created_at.desc()))
    invites = result.scalars().all()
    return {
        "total": len(invites),
        "invites": [InviteResponse.from_orm(i).model_dump() for i in invites],
    }


# ── Feature Flags ──────────────────────────────────────────────────────────────


@router.get("/features", dependencies=[Depends(_require_admin)])
async def list_features() -> dict:
    """Lista os feature flags atuais (defaults de env + overrides em memória)."""
    return {"flags": get_flags()}


@router.patch("/features/{name}", dependencies=[Depends(_require_admin)])
async def toggle_feature(name: str, body: FeatureFlagPatch) -> dict:
    """Alterna um feature flag em memória (reset no próximo restart do servidor)."""
    try:
        set_flag(name, body.enabled)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{name}' não encontrado. "
            f"Flags disponíveis: {list(get_flags().keys())}",
        )
    return {"name": name, "enabled": body.enabled}

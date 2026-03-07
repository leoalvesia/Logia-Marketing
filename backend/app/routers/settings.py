"""Router de configurações do usuário — perfis monitorados e conta."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.cache.redis_cache import cache_get, cache_invalidate, cache_set
from app.database import get_db
from app.models.monitored_profiles import MonitoredProfile
from app.models.user import User

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

_VALID_PLATFORMS = {"instagram", "youtube", "linkedin", "twitter"}


class AddProfileRequest(BaseModel):
    platform: str
    handle: str
    url: Optional[str] = None


# ── Serializer ────────────────────────────────────────────────────────────────


def _profile_to_dict(p: MonitoredProfile) -> dict[str, Any]:
    return {
        "id": p.id,
        "platform": p.platform,
        "handle": p.handle,
        "url": p.url,
        "active": p.active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_profile_or_404(
    profile_id: str, user_id: str, db: AsyncSession
) -> MonitoredProfile:
    result = await db.execute(
        select(MonitoredProfile).where(
            MonitoredProfile.id == profile_id,
            MonitoredProfile.user_id == user_id,
        )
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado"
        )
    return profile


# ── Perfis monitorados ────────────────────────────────────────────────────────


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def add_monitored_profile(
    body: AddProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.platform not in _VALID_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Plataforma inválida: {body.platform!r}. Válidas: {sorted(_VALID_PLATFORMS)}",
        )

    handle = body.handle.lstrip("@")
    profile = MonitoredProfile(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        platform=body.platform,
        handle=handle,
        url=body.url,
        active=True,
    )
    db.add(profile)
    await db.commit()
    return _profile_to_dict(profile)


@router.get("/profiles")
async def list_monitored_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = f"logia:profiles:{current_user.id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(MonitoredProfile)
        .where(MonitoredProfile.user_id == current_user.id)
        .order_by(MonitoredProfile.created_at.desc())
    )
    profiles = result.scalars().all()
    response = {"profiles": [_profile_to_dict(p) for p in profiles]}
    await cache_set(cache_key, response, ttl=300)
    return response


@router.patch("/profiles/{profile_id}/toggle")
async def toggle_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await _get_profile_or_404(profile_id, current_user.id, db)
    profile.active = not profile.active
    await db.commit()
    await cache_invalidate(f"logia:profiles:{current_user.id}")
    return _profile_to_dict(profile)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await _get_profile_or_404(profile_id, current_user.id, db)
    await db.delete(profile)
    await db.commit()
    await cache_invalidate(f"logia:profiles:{current_user.id}")


# ── Stubs existentes ──────────────────────────────────────────────────────────


@router.get("/social-accounts")
async def list_social_accounts():
    # TODO: status de conexão das contas sociais
    return {"accounts": []}


@router.get("/brand")
async def get_brand_identity():
    # TODO: identidade visual do usuário (cores, fontes, logo)
    return {"brand": {}}


@router.get("/persona")
async def get_persona():
    # TODO: nicho/persona do usuário
    return {"persona": {}}

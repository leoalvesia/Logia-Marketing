"""Router da biblioteca de conteúdo — copies, artes e posts por pipeline."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.cache.redis_cache import cache_get, cache_invalidate, cache_set
from app.database import get_db
from app.models.art import Art, ArtType
from app.models.copy import Copy, CopyChannel, CopyStatus
from app.models.pipeline import Pipeline
from app.models.user import User

router = APIRouter()


# ── Serializers ───────────────────────────────────────────────────────────────


def _copy_to_dict(c: Copy) -> dict[str, Any]:
    try:
        content = json.loads(c.content) if c.content else {}
    except (json.JSONDecodeError, TypeError):
        content = {}
    return {
        "id": c.id,
        "pipeline_id": c.pipeline_id,
        "channel": c.channel.value,
        "status": c.status.value,
        "content": content,
        "source_url": c.source_url,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _art_to_dict(a: Art) -> dict[str, Any]:
    try:
        image_urls = json.loads(a.image_urls) if a.image_urls else []
    except (json.JSONDecodeError, TypeError):
        image_urls = []
    return {
        "id": a.id,
        "copy_id": a.copy_id,
        "pipeline_id": a.pipeline_id,
        "type": a.art_type.value,
        "image_urls": image_urls,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_copy_or_404(copy_id: str, user_id: str, db: AsyncSession) -> Copy:
    result = await db.execute(
        select(Copy)
        .join(Pipeline, Copy.pipeline_id == Pipeline.id)
        .where(Copy.id == copy_id)
        .where(Pipeline.user_id == user_id)
    )
    copy = result.scalar_one_or_none()
    if copy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Copy não encontrada")
    return copy


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/copies")
async def list_copies(
    channel: Optional[str] = Query(None, description="Filtro por canal (instagram, linkedin, …)"),
    copy_status: Optional[str] = Query(None, alias="status", description="Filtro por status"),
    created_after: Optional[str] = Query(None, description="ISO datetime mínimo"),
    created_before: Optional[str] = Query(None, description="ISO datetime máximo"),
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Cache apenas para requests sem filtros de data (fácil de invalidar)
    use_cache = not created_after and not created_before
    cache_key = (
        f"logia:copies:{current_user.id}"
        f":ch={channel or ''}:st={copy_status or ''}"
        f":p={page}:pp={per_page}"
    )
    if use_cache:
        cached = await cache_get(cache_key)
        if cached:
            return cached

    q = (
        select(Copy)
        .join(Pipeline, Copy.pipeline_id == Pipeline.id)
        .where(Pipeline.user_id == current_user.id)
        .where(Copy.status != CopyStatus.DELETED)
    )

    if channel:
        try:
            q = q.where(Copy.channel == CopyChannel(channel))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Canal inválido: {channel!r}")

    if copy_status:
        try:
            q = q.where(Copy.status == CopyStatus(copy_status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {copy_status!r}")

    if created_after:
        try:
            q = q.where(Copy.created_at >= datetime.fromisoformat(created_after))
        except ValueError:
            raise HTTPException(status_code=400, detail="created_after inválido (use ISO 8601)")

    if created_before:
        try:
            q = q.where(Copy.created_at <= datetime.fromisoformat(created_before))
        except ValueError:
            raise HTTPException(status_code=400, detail="created_before inválido (use ISO 8601)")

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        q.order_by(Copy.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    copies = result.scalars().all()

    response = {
        "copies": [_copy_to_dict(c) for c in copies],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
    }

    if use_cache:
        await cache_set(cache_key, response, ttl=60)

    return response


@router.get("/arts")
async def list_arts(
    art_type: Optional[str] = Query(None, alias="type", description="Filtro por tipo: static, carousel, thumbnail"),
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(Art)
        .join(Pipeline, Art.pipeline_id == Pipeline.id)
        .where(Pipeline.user_id == current_user.id)
    )

    if art_type:
        try:
            q = q.where(Art.art_type == ArtType(art_type))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {art_type!r}")

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        q.order_by(Art.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    arts = result.scalars().all()

    return {
        "arts": [_art_to_dict(a) for a in arts],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
    }


@router.get("/posts")
async def list_posts(
    page: int = Query(1, ge=1, description="Número da página (pipelines)"),
    per_page: int = Query(20, ge=1, le=100, description="Pipelines por página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna pipelines do usuário com copies e artes agrupadas."""
    # Total de pipelines para paginação
    total_result = await db.execute(
        select(func.count(Pipeline.id)).where(Pipeline.user_id == current_user.id)
    )
    total = total_result.scalar_one()

    pipelines_result = await db.execute(
        select(Pipeline)
        .where(Pipeline.user_id == current_user.id)
        .order_by(Pipeline.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    pipelines = pipelines_result.scalars().all()

    if not pipelines:
        return {"posts": [], "total": total, "page": page, "per_page": per_page, "has_next": False}

    pipeline_ids = [p.id for p in pipelines]

    # Copies e arts em paralelo — queries independentes no mesmo evento loop.
    # SQLAlchemy async serializa internamente na mesma conexão, mas a estrutura
    # está pronta para escalar com connection pool em produção.
    copies_result, arts_result = await asyncio.gather(
        db.execute(
            select(Copy)
            .where(Copy.pipeline_id.in_(pipeline_ids))
            .where(Copy.status != CopyStatus.DELETED)
        ),
        db.execute(
            select(Art).where(Art.pipeline_id.in_(pipeline_ids))
        ),
    )

    copies_by_pipeline: dict[str, list] = {}
    for c in copies_result.scalars():
        copies_by_pipeline.setdefault(c.pipeline_id, []).append(_copy_to_dict(c))

    arts_by_pipeline: dict[str, list] = {}
    for a in arts_result.scalars():
        arts_by_pipeline.setdefault(a.pipeline_id, []).append(_art_to_dict(a))

    posts = [
        {
            "pipeline_id": p.id,
            "copies": copies_by_pipeline.get(p.id, []),
            "arts": arts_by_pipeline.get(p.id, []),
        }
        for p in pipelines
    ]
    return {
        "posts": posts,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
    }


@router.patch("/copies/{copy_id}/approve")
async def approve_copy(
    copy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    copy = await _get_copy_or_404(copy_id, current_user.id, db)
    if copy.status == CopyStatus.DELETED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Copy não encontrada")
    copy.status = CopyStatus.APPROVED
    await db.commit()
    await cache_invalidate(f"logia:copies:{current_user.id}:*")
    return _copy_to_dict(copy)


@router.delete("/copies/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_copy(
    copy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    copy = await _get_copy_or_404(copy_id, current_user.id, db)
    copy.status = CopyStatus.DELETED
    await db.commit()
    await cache_invalidate(f"logia:copies:{current_user.id}:*")

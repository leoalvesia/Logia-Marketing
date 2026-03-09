"""Router do pipeline de conteúdo."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.pipeline import Pipeline, PipelineState
from app.models.topic import Topic
from app.models.user import User
from app.tasks import generate_art, generate_copy, publish_post, run_pipeline_research
from app.ws_manager import manager

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class StartPipelineRequest(BaseModel):
    channels: list[str] = []


class SelectTopicRequest(BaseModel):
    topic_id: str


class ApproveArtRequest(BaseModel):
    schedule: bool = False  # False = publicar agora, True = agendar


class PublishRequest(BaseModel):
    schedule: bool = False
    scheduled_at: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_pipeline_or_404(session_id: str, user_id: str, db: AsyncSession) -> Pipeline:
    result = await db.execute(
        select(Pipeline).where(Pipeline.id == session_id, Pipeline.user_id == user_id)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline não encontrado",
        )
    return pipeline


async def _emit_state(pipeline: Pipeline) -> None:
    await manager.send(
        pipeline.id,
        {
            "state": pipeline.state.value,
            "data": {},
            "timestamp": _now_iso(),
        },
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_pipeline(
    body: StartPipelineRequest = StartPipelineRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = Pipeline(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        state=PipelineState.RESEARCHING,
        channels_selected=json.dumps(body.channels),
    )
    db.add(pipeline)
    await db.commit()
    await _emit_state(pipeline)

    # Dispara pesquisa assíncrona no Celery
    run_pipeline_research.delay(pipeline.id, current_user.id)

    return {"session_id": pipeline.id, "state": pipeline.state.value}


@router.get("/{session_id}/topics")
async def get_pipeline_topics(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna os temas gerados para o pipeline, ordenados por rank."""
    await _get_pipeline_or_404(session_id, current_user.id, db)
    result = await db.execute(
        select(Topic).where(Topic.pipeline_id == session_id).order_by(Topic.rank)
    )
    topics = result.scalars().all()
    return {
        "topics": [
            {
                "id": t.id,
                "title": t.title,
                "summary": t.summary,
                "source_url": t.source_url,
                "source_verified": t.source_verified,
                "channels_found": json.loads(t.channels_found or "[]"),
                "score": t.score,
                "rank": t.rank,
                "dados_pesquisa": getattr(t, "dados_pesquisa", ""),
                "published_at": t.published_at.isoformat() if t.published_at else None,
            }
            for t in topics
        ]
    }


@router.get("/{session_id}")
async def get_pipeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await _get_pipeline_or_404(session_id, current_user.id, db)
    return {
        "session_id": pipeline.id,
        "state": pipeline.state.value,
        "topic_selected": pipeline.topic_selected,
        "channels_selected": pipeline.channels_selected,
        "error_detail": pipeline.error_detail,
        "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
        "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
    }


@router.post("/{session_id}/select-topic")
async def select_topic(
    session_id: str,
    body: SelectTopicRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await _get_pipeline_or_404(session_id, current_user.id, db)
    pipeline.topic_selected = body.topic_id
    pipeline.state = PipelineState.GENERATING_COPY
    await db.commit()
    await _emit_state(pipeline)

    # Dispara geração de copy para todos os canais selecionados
    channels = json.loads(pipeline.channels_selected or "[]")
    if not channels:
        channels = ["instagram", "linkedin", "twitter", "youtube", "email"]
    generate_copy.delay(session_id, channels)

    return {"session_id": pipeline.id, "state": pipeline.state.value}


@router.post("/{session_id}/approve-copy")
async def approve_copy(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await _get_pipeline_or_404(session_id, current_user.id, db)
    pipeline.state = PipelineState.GENERATING_ART
    await db.commit()
    await _emit_state(pipeline)

    # Dispara geração de arte (agentes de arte a implementar)
    generate_art.delay(session_id, "static")

    return {"session_id": pipeline.id, "state": pipeline.state.value}


@router.post("/{session_id}/approve-art")
async def approve_art(
    session_id: str,
    body: ApproveArtRequest = ApproveArtRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await _get_pipeline_or_404(session_id, current_user.id, db)
    pipeline.state = PipelineState.SCHEDULED if body.schedule else PipelineState.PUBLISHING
    await db.commit()
    await _emit_state(pipeline)

    # Dispara publicação (publishers a implementar)
    channels = json.loads(pipeline.channels_selected or "[]")
    if not body.schedule and channels:
        publish_post.delay(session_id, channels)

    return {"session_id": pipeline.id, "state": pipeline.state.value}


@router.post("/{session_id}/publish")
async def publish(
    session_id: str,
    body: PublishRequest = PublishRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publica ou agenda o post. Chamado pelo frontend após aprovação da arte."""
    pipeline = await _get_pipeline_or_404(session_id, current_user.id, db)
    pipeline.state = PipelineState.SCHEDULED if body.schedule else PipelineState.PUBLISHING
    await db.commit()
    await _emit_state(pipeline)

    channels = json.loads(pipeline.channels_selected or "[]")
    if not body.schedule and channels:
        publish_post.delay(session_id, channels)

    return {"session_id": pipeline.id, "state": pipeline.state.value}

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
from app.models.user import User
from app.ws_manager import manager

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class StartPipelineRequest(BaseModel):
    channels: list[str] = []


class SelectTopicRequest(BaseModel):
    topic_id: str


class ApproveArtRequest(BaseModel):
    schedule: bool = False  # False = publicar agora, True = agendar


# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_pipeline_or_404(
    session_id: str, user_id: str, db: AsyncSession
) -> Pipeline:
    result = await db.execute(
        select(Pipeline).where(
            Pipeline.id == session_id, Pipeline.user_id == user_id
        )
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
    return {"session_id": pipeline.id, "state": pipeline.state.value}


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
    return {"session_id": pipeline.id, "state": pipeline.state.value}


@router.post("/{session_id}/approve-art")
async def approve_art(
    session_id: str,
    body: ApproveArtRequest = ApproveArtRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pipeline = await _get_pipeline_or_404(session_id, current_user.id, db)
    pipeline.state = (
        PipelineState.SCHEDULED if body.schedule else PipelineState.PUBLISHED
    )
    await db.commit()
    await _emit_state(pipeline)
    return {"session_id": pipeline.id, "state": pipeline.state.value}

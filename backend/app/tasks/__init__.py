"""Tarefas Celery — pesquisa diária e geração de copy em paralelo."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from celery import group

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


# ── Helpers async (executados via asyncio.run dentro das tasks síncronas) ────


async def _persist_copy(pipeline_id: str, channel: str, result: dict) -> str:
    """Persiste a copy no banco e retorna o ID gerado."""
    from app.database import AsyncSessionLocal
    from app.models.copy import Copy, CopyChannel, CopyStatus

    copy_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        copy = Copy(
            id=copy_id,
            pipeline_id=pipeline_id,
            channel=CopyChannel(channel),
            content=json.dumps(result, ensure_ascii=False),
            source_url=result.get("source_url", ""),
            status=CopyStatus.DRAFT,
        )
        session.add(copy)
        await session.commit()
    return copy_id


async def _emit_copy_update(pipeline_id: str, channel: str, copy_id: str) -> None:
    """Emite evento WebSocket para o pipeline informando copy concluída."""
    from app.ws_manager import manager

    await manager.send(
        pipeline_id,
        {
            "state": "GENERATING_COPY",
            "data": {"channel": channel, "copy_id": copy_id},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def _emit_copy_chunk(pipeline_id: str, channel: str, chunk: str) -> None:
    """Emite chunk de streaming via WebSocket.

    Nota arquitetural: em produção com workers Celery separados do servidor
    FastAPI, o WebSocket manager não terá a conexão ativa. Para streaming
    real em produção, publique os chunks em Redis pub/sub e faça o servidor
    FastAPI subscrever e encaminhar ao WebSocket do cliente.
    """
    from app.ws_manager import manager

    await manager.send(
        pipeline_id,
        {
            "type": "copy_chunk",
            "channel": channel,
            "chunk": chunk,
        },
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────


@celery_app.task(name="app.tasks.generate_single_copy", bind=True, max_retries=3)
def generate_single_copy(self, pipeline_id: str, channel: str, context: dict):
    """Gera copy para um canal com streaming, salva no banco e emite WebSocket.

    Usa streaming do Claude para emitir chunks em tempo real via WebSocket.
    Retry automático 3× com backoff exponencial (2s, 4s, 8s) em falha de API.

    Args:
        pipeline_id: ID da sessão de pipeline.
        channel: Canal alvo ('instagram', 'linkedin', 'twitter', 'youtube', 'email').
        context: Contexto do tema (tema, resumo, link_origem, nicho_usuario, etc.).
    """
    try:
        from app.agents.copy import get_agent

        agent = get_agent(channel)

        def _on_chunk(chunk: str) -> None:
            """Emite cada chunk de texto recebido do Claude via WebSocket."""
            try:
                asyncio.run(_emit_copy_chunk(pipeline_id, channel, chunk))
            except Exception:
                pass  # emissão de chunk nunca aborta a geração

        result = agent.generate_streaming(context, on_chunk=_on_chunk)

        copy_id = asyncio.run(_persist_copy(pipeline_id, channel, result))
        asyncio.run(_emit_copy_update(pipeline_id, channel, copy_id))

        logger.info("generate_single_copy: %s concluído — copy_id=%s", channel, copy_id)
        return {"channel": channel, "copy_id": copy_id}

    except Exception as exc:
        logger.error("generate_single_copy [%s]: %s", channel, exc)
        # Backoff exponencial: 2^retry segundos (2s, 4s, 8s)
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(name="app.tasks.generate_all_copies")
def generate_all_copies(pipeline_id: str, channels: list[str], context: dict):
    """Dispara geração de copy em paralelo para todos os canais selecionados.

    Usa Celery group() para execução paralela — cada canal é uma task independente.

    Args:
        pipeline_id: ID da sessão de pipeline.
        channels: Lista de canais (ex.: ['instagram', 'linkedin']).
        context: Contexto do tema a ser transformado em copy.
    """
    parallel = group(
        generate_single_copy.s(pipeline_id, channel, context)
        for channel in channels
    )
    parallel.apply_async()
    logger.info(
        "generate_all_copies: %d tasks disparadas para pipeline %s",
        len(channels),
        pipeline_id,
    )


# ── Stubs existentes ──────────────────────────────────────────────────────────


@celery_app.task(name="app.tasks.run_daily_research")
def run_daily_research():
    """Executa pesquisa diária de tendências para todos os usuários."""
    # TODO: implementar coleta por canal e orquestração
    pass


@celery_app.task(name="app.tasks.generate_copy")
def generate_copy(pipeline_id: str, channels: list[str]):
    """Atalho para generate_all_copies sem contexto pré-montado."""
    # TODO: buscar contexto do banco e delegar para generate_all_copies
    pass


@celery_app.task(name="app.tasks.generate_art")
def generate_art(pipeline_id: str, art_type: str):
    """Gera arte (estática, carrossel ou thumbnail)."""
    # TODO: implementar agentes de arte
    pass


@celery_app.task(name="app.tasks.publish_post")
def publish_post(pipeline_id: str, channels: list[str]):
    """Publica post nos canais selecionados."""
    # TODO: implementar publishers por canal
    pass

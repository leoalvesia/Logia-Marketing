"""Tarefas Celery — pesquisa diária e geração de copy em paralelo."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from celery import chord

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
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(name="app.tasks.finalize_copy_review")
def finalize_copy_review(results: list, pipeline_id: str):
    """Callback do chord: chamado quando todas as copies de um pipeline foram geradas.

    Avança o pipeline para COPY_REVIEW e emite evento WebSocket.
    """
    from app.ws_manager import manager

    asyncio.run(_update_pipeline_state(pipeline_id, "COPY_REVIEW"))
    asyncio.run(
        manager.send(
            pipeline_id,
            {
                "state": "COPY_REVIEW",
                "data": {"copies_generated": len(results)},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    )
    logger.info(
        "finalize_copy_review: pipeline=%s copies=%d → COPY_REVIEW",
        pipeline_id,
        len(results),
    )


@celery_app.task(name="app.tasks.generate_all_copies")
def generate_all_copies(pipeline_id: str, channels: list[str], context: dict):
    """Dispara geração de copy em paralelo para todos os canais.

    Usa Celery chord() para execução paralela com callback que avança o
    pipeline para COPY_REVIEW quando todas as copies estiverem prontas.
    """
    tasks = [generate_single_copy.s(pipeline_id, channel, context) for channel in channels]
    chord(tasks)(finalize_copy_review.s(pipeline_id))
    logger.info(
        "generate_all_copies: chord de %d tasks disparado — pipeline=%s",
        len(channels),
        pipeline_id,
    )


# ── Helpers de pesquisa ───────────────────────────────────────────────────────


def _run_collector(platform: str, handle: str) -> list[dict]:
    """Chama o coletor correto para a plataforma. Retorna lista vazia em erro."""
    try:
        if platform == "instagram":
            from app.agents.research.instagram_collector import collect
        elif platform == "youtube":
            from app.agents.research.youtube_collector import collect
        elif platform == "twitter":
            from app.agents.research.twitter_collector import collect
        elif platform == "linkedin":
            from app.agents.research.linkedin_collector import collect
        else:
            return []
        return collect(handle)
    except Exception as exc:
        logger.warning("_run_collector [%s/%s]: %s", platform, handle, exc)
        return []


async def _fetch_profiles_and_user(pipeline_id: str, user_id: str):
    """Retorna (user, profiles) do banco para o pipeline dado."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.monitored_profiles import MonitoredProfile

    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()

        profiles_res = await session.execute(
            select(MonitoredProfile).where(
                MonitoredProfile.user_id == user_id,
                MonitoredProfile.active.is_(True),
            )
        )
        profiles = profiles_res.scalars().all()
        return user, list(profiles)


async def _save_topics(pipeline_id: str, user_id: str, topics: list[dict]) -> None:
    """Persiste os temas gerados pelo orquestrador no banco."""
    from app.database import AsyncSessionLocal
    from app.models.topic import Topic

    async with AsyncSessionLocal() as session:
        for rank, t in enumerate(topics, start=1):
            # Orchestrator retorna chaves em PT ("titulo", "resumo", "link_origem",
            # "plataformas", "publicado_em"). Suporte a ambas as formas para
            # compatibilidade com testes e futuras refatorações.
            topic = Topic(
                id=str(uuid.uuid4()),
                pipeline_id=pipeline_id,
                user_id=user_id,
                title=t.get("title") or t.get("titulo", ""),
                summary=t.get("summary") or t.get("resumo", ""),
                source_url=t.get("source_url") or t.get("link_origem", ""),
                source_verified=t.get("source_verified", False),
                channels_found=json.dumps(t.get("platforms") or t.get("plataformas", [])),
                score=t.get("score", 0.0),
                rank=rank,
                dados_pesquisa=t.get("dados_pesquisa", ""),
            )
            session.add(topic)
        await session.commit()


async def _update_pipeline_state(pipeline_id: str, state: str, error: str | None = None) -> None:
    """Atualiza o estado do pipeline no banco."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.pipeline import Pipeline, PipelineState

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
        pipeline = res.scalar_one_or_none()
        if pipeline:
            pipeline.state = PipelineState(state)
            if error:
                pipeline.error_detail = error
            await session.commit()


async def _fetch_pipeline_context(pipeline_id: str):
    """Retorna (pipeline, topic, user) para montar contexto de copy."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.pipeline import Pipeline
    from app.models.topic import Topic
    from app.models.user import User

    async with AsyncSessionLocal() as session:
        pipeline_res = await session.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
        pipeline = pipeline_res.scalar_one_or_none()
        if not pipeline:
            return None, None, None

        topic = None
        if pipeline.topic_selected:
            topic_res = await session.execute(
                select(Topic).where(Topic.id == pipeline.topic_selected)
            )
            topic = topic_res.scalar_one_or_none()

        user_res = await session.execute(select(User).where(User.id == pipeline.user_id))
        user = user_res.scalar_one_or_none()
        return pipeline, topic, user


# ── Tasks ─────────────────────────────────────────────────────────────────────


@celery_app.task(name="app.tasks.run_pipeline_research", bind=True, max_retries=2)
def run_pipeline_research(self, pipeline_id: str, user_id: str):
    """Coleta conteúdo dos perfis monitorados, orquestra e salva temas no banco.

    Fluxo:
        1. Busca perfis ativos do usuário no banco.
        2. Executa coletores em paralelo (ThreadPoolExecutor).
        3. Passa resultados brutos para o orquestrador (score + dedup).
        4. Salva até 10 temas no banco.
        5. Avança pipeline para AWAITING_SELECTION e emite WS.
    """
    try:
        from app.agents.research.orchestrator import orchestrate
        from app.ws_manager import manager

        user, profiles = asyncio.run(_fetch_profiles_and_user(pipeline_id, user_id))
        if not user:
            logger.error("run_pipeline_research: user %s não encontrado", user_id)
            return

        nicho = user.nicho or "marketing digital"
        raw_results: list[dict] = []

        if profiles:
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(_run_collector, p.platform, p.handle): p for p in profiles}
                for future in as_completed(futures):
                    try:
                        raw_results.extend(future.result())
                    except Exception as exc:
                        logger.warning("run_pipeline_research coletor falhou: %s", exc)

        topics = orchestrate(raw_results, nicho)

        if topics:
            asyncio.run(_save_topics(pipeline_id, user_id, topics))

        asyncio.run(_update_pipeline_state(pipeline_id, "AWAITING_SELECTION"))

        asyncio.run(
            manager.send(
                pipeline_id,
                {
                    "state": "AWAITING_SELECTION",
                    "data": {"topics_count": len(topics)},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        )

        logger.info("run_pipeline_research: pipeline=%s temas=%d", pipeline_id, len(topics))

    except Exception as exc:
        logger.error("run_pipeline_research [%s]: %s", pipeline_id, exc)
        asyncio.run(_update_pipeline_state(pipeline_id, "FAILED", str(exc)))
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(name="app.tasks.run_daily_research")
def run_daily_research():
    """Executa pesquisa diária de tendências para todos os usuários ativos."""
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.user import User
        import uuid as _uuid

        async def _get_active_users():
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(User).where(User.deleted_at.is_(None)))
                return res.scalars().all()

        async def _create_research_pipeline(user_id: str) -> str:
            """Cria um pipeline de pesquisa diária no banco e retorna o ID."""
            from app.models.pipeline import Pipeline, PipelineState

            pid = str(_uuid.uuid4())
            async with AsyncSessionLocal() as session:
                pipeline = Pipeline(
                    id=pid,
                    user_id=user_id,
                    state=PipelineState.RESEARCHING,
                    channels_selected=json.dumps([]),
                )
                session.add(pipeline)
                await session.commit()
            return pid

        users = asyncio.run(_get_active_users())
        for user in users:
            pipeline_id = asyncio.run(_create_research_pipeline(user.id))
            run_pipeline_research.delay(pipeline_id, user.id)

        logger.info("run_daily_research: disparado para %d usuários", len(users))

    except Exception as exc:
        logger.error("run_daily_research: %s", exc)


@celery_app.task(name="app.tasks.generate_copy", bind=True, max_retries=2)
def generate_copy(self, pipeline_id: str, channels: list[str]):
    """Busca contexto do banco e delega para generate_all_copies."""
    try:
        pipeline, topic, user = asyncio.run(_fetch_pipeline_context(pipeline_id))

        if not pipeline or not topic or not user:
            logger.error(
                "generate_copy: dados incompletos — pipeline=%s topic=%s",
                pipeline_id,
                pipeline.topic_selected if pipeline else None,
            )
            asyncio.run(_update_pipeline_state(pipeline_id, "FAILED", "Contexto incompleto"))
            return

        context = {
            "tema": topic.title,
            "resumo": topic.summary,
            "link_origem": topic.source_url,
            "dados_pesquisa": getattr(topic, "dados_pesquisa", ""),
            "nicho_usuario": user.nicho or "",
            "persona_usuario": user.persona or "",
            "channels": channels,
        }

        generate_all_copies.delay(pipeline_id, channels, context)
        logger.info(
            "generate_copy: delegado para %d canais — pipeline=%s",
            len(channels),
            pipeline_id,
        )

    except Exception as exc:
        logger.error("generate_copy [%s]: %s", pipeline_id, exc)
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


async def _fetch_copies_for_pipeline(pipeline_id: str) -> list:
    """Retorna todas as copies aprovadas/draft do pipeline."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.copy import Copy, CopyStatus

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(Copy).where(
                Copy.pipeline_id == pipeline_id,
                Copy.status.in_([CopyStatus.DRAFT, CopyStatus.APPROVED]),
            )
        )
        return res.scalars().all()


async def _persist_art(
    pipeline_id: str,
    copy_id: str,
    art_type: str,
    image_urls: list[str],
) -> str:
    """Salva registro de arte no banco e retorna o ID."""
    from app.database import AsyncSessionLocal
    from app.models.art import Art, ArtType

    art_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        art = Art(
            id=art_id,
            copy_id=copy_id,
            pipeline_id=pipeline_id,
            art_type=ArtType(art_type),
            image_urls=json.dumps(image_urls, ensure_ascii=False),
        )
        session.add(art)
        await session.commit()
    return art_id


@celery_app.task(name="app.tasks.generate_art", bind=True, max_retries=2)
def generate_art(self, pipeline_id: str, art_type: str = "static"):
    """Gera arte para todas as copies do pipeline e salva URLs no banco.

    Fluxo:
        1. Busca copies do pipeline no banco.
        2. Para cada copy, gera imagem via Stability AI (ou placeholder em dev).
        3. Faz upload para Google Drive e salva Art record no banco.
        4. Avança pipeline para ART_REVIEW e emite WS.
    """
    try:
        from app.agents.art import get_agent
        from app.ws_manager import manager

        copies = asyncio.run(_fetch_copies_for_pipeline(pipeline_id))

        if not copies:
            logger.warning("generate_art: nenhuma copy encontrada para pipeline=%s", pipeline_id)
            asyncio.run(_update_pipeline_state(pipeline_id, "ART_REVIEW"))
            return

        agent = get_agent(art_type)
        art_ids: list[str] = []

        for copy in copies:
            try:
                # Extrai texto legível do conteúdo JSON da copy
                copy_content = (
                    json.loads(copy.content) if isinstance(copy.content, str) else copy.content
                )
                copy_text = (
                    copy_content.get("caption")
                    or copy_content.get("post")
                    or (
                        copy_content.get("tweets", [""])[0]
                        if isinstance(copy_content.get("tweets"), list)
                        else ""
                    )
                    or copy_content.get("subject")
                    or copy_content.get("roteiro")
                    or ""
                )

                image_urls = agent.generate(
                    pipeline_id=pipeline_id,
                    copy_id=copy.id,
                    copy_text=copy_text,
                    channel=(
                        copy.channel.value if hasattr(copy.channel, "value") else str(copy.channel)
                    ),
                )

                art_id = asyncio.run(_persist_art(pipeline_id, copy.id, art_type, image_urls))
                art_ids.append(art_id)
                logger.info("generate_art: art_id=%s urls=%d", art_id, len(image_urls))

            except Exception as exc:
                logger.error("generate_art copy=%s: %s", copy.id, exc)

        asyncio.run(_update_pipeline_state(pipeline_id, "ART_REVIEW"))
        asyncio.run(
            manager.send(
                pipeline_id,
                {
                    "state": "ART_REVIEW",
                    "data": {"art_ids": art_ids, "art_type": art_type},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        )

        logger.info("generate_art: pipeline=%s arts=%d", pipeline_id, len(art_ids))

    except Exception as exc:
        logger.error("generate_art [%s]: %s", pipeline_id, exc)
        asyncio.run(_update_pipeline_state(pipeline_id, "FAILED", str(exc)))
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(name="app.tasks.publish_post")
def publish_post(pipeline_id: str, channels: list[str]):
    """Publica post nos canais selecionados. Publishers pendentes de implementação."""
    logger.info(
        "publish_post: pipeline=%s channels=%s — publishers ainda não implementados",
        pipeline_id,
        channels,
    )
    # Quando os publishers estiverem prontos:
    # from app.publishers.instagram import publish as publish_ig
    # from app.publishers.linkedin import publish as publish_li
    # ...

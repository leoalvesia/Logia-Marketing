"""Factory functions para objetos PipelineSession.

Uso:
    from tests.factories.pipeline_factory import create_mock_pipeline

    pipeline = create_mock_pipeline()  # estado RESEARCHING
    pipeline_ready = create_mock_pipeline(state="AWAITING_SELECTION")
"""

from __future__ import annotations

import uuid

from app.models.pipeline import Pipeline, PipelineState


def create_mock_pipeline(
    state: str | PipelineState = PipelineState.RESEARCHING,
    user_id: str | None = None,
    pipeline_id: str | None = None,
    channels_selected: list[str] | None = None,
) -> Pipeline:
    """
    Cria um objeto Pipeline em memória (não persiste no banco).

    Args:
        state: Estado do pipeline. Aceita PipelineState enum ou string
               (ex.: 'RESEARCHING', 'AWAITING_SELECTION').
        user_id: ID do usuário associado. Gera UUID aleatório se None.
        pipeline_id: ID do pipeline. Gera UUID aleatório se None.
        channels_selected: Lista de canais selecionados (JSON array).
                           Default: ['instagram', 'linkedin'].

    Returns:
        Objeto Pipeline pronto para uso em testes.
    """
    if isinstance(state, str):
        state = PipelineState(state)

    if channels_selected is None:
        channels_selected = ["instagram", "linkedin"]

    import json

    return Pipeline(
        id=pipeline_id or str(uuid.uuid4()),
        user_id=user_id or str(uuid.uuid4()),
        state=state,
        channels_selected=json.dumps(channels_selected),
    )


def create_mock_pipeline_in_state(state_name: str) -> Pipeline:
    """
    Atalho para criar pipeline em um estado específico pelo nome.

    Args:
        state_name: Nome do estado como string (ex.: 'COPY_REVIEW').

    Returns:
        Pipeline no estado especificado.
    """
    return create_mock_pipeline(state=state_name)

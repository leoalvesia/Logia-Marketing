"""Máquina de estados do pipeline de conteúdo.

Implementa as transições válidas definidas no PRD seção 4.
"""

from __future__ import annotations

from app.models.pipeline import PipelineState


class InvalidStateTransitionError(Exception):
    """Lançada quando uma transição de estado inválida é tentada."""


# Mapa de transições válidas: estado atual → frozenset de estados permitidos.
# Todas as transições não listadas aqui são inválidas.
VALID_TRANSITIONS: dict[PipelineState, frozenset[PipelineState]] = {
    PipelineState.RESEARCHING: frozenset({
        PipelineState.ORCHESTRATING,
        PipelineState.FAILED,
    }),
    PipelineState.ORCHESTRATING: frozenset({
        PipelineState.AWAITING_SELECTION,
        PipelineState.FAILED,
    }),
    PipelineState.AWAITING_SELECTION: frozenset({
        PipelineState.GENERATING_COPY,
        PipelineState.FAILED,
    }),
    PipelineState.GENERATING_COPY: frozenset({
        PipelineState.COPY_REVIEW,
        PipelineState.FAILED,
    }),
    PipelineState.COPY_REVIEW: frozenset({
        PipelineState.GENERATING_ART,
        PipelineState.SCHEDULED,   # atalho: pular geração de arte
        PipelineState.FAILED,
    }),
    PipelineState.GENERATING_ART: frozenset({
        PipelineState.ART_REVIEW,
        PipelineState.FAILED,
    }),
    PipelineState.ART_REVIEW: frozenset({
        PipelineState.SCHEDULED,
        PipelineState.PUBLISHING,  # publicação imediata sem agendamento
        PipelineState.FAILED,
    }),
    PipelineState.SCHEDULED: frozenset({
        PipelineState.PUBLISHING,
        PipelineState.FAILED,
    }),
    PipelineState.PUBLISHING: frozenset({
        PipelineState.PUBLISHED,
        PipelineState.FAILED,
    }),
    PipelineState.PUBLISHED: frozenset(),   # estado terminal
    PipelineState.FAILED: frozenset({
        PipelineState.RESEARCHING,          # retry
    }),
}


def transition(current: PipelineState, target: PipelineState) -> PipelineState:
    """Valida e executa uma transição de estado.

    Args:
        current: estado atual do pipeline.
        target: estado desejado.

    Returns:
        O estado alvo (igual a ``target``).

    Raises:
        InvalidStateTransitionError: se a transição não for permitida.
    """
    allowed = VALID_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        allowed_names = sorted(s.value for s in allowed)
        raise InvalidStateTransitionError(
            f"Transição inválida: {current.value!r} → {target.value!r}. "
            f"Permitidas a partir de {current.value!r}: {allowed_names or ['nenhuma']}"
        )
    return target


def get_allowed_transitions(state: PipelineState) -> list[PipelineState]:
    """Retorna lista ordenada de estados permitidos a partir do estado atual."""
    return sorted(
        VALID_TRANSITIONS.get(state, frozenset()),
        key=lambda s: s.value,
    )

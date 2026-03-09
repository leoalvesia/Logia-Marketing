"""Factory de agentes de arte."""

from __future__ import annotations

from app.agents.art.static import StaticArtAgent
from app.agents.art.carousel import CarouselArtAgent
from app.agents.art.thumbnail import ThumbnailArtAgent
from app.agents.art.base import ArtAgent

_AGENTS: dict[str, type[ArtAgent]] = {
    "static": StaticArtAgent,
    "carousel": CarouselArtAgent,
    "thumbnail": ThumbnailArtAgent,
}


def get_agent(art_type: str) -> ArtAgent:
    """Retorna a instância do agente para o tipo de arte solicitado.

    Args:
        art_type: "static" | "carousel" | "thumbnail"

    Returns:
        Instância do agente correspondente. Padrão: StaticArtAgent.
    """
    cls = _AGENTS.get(art_type, StaticArtAgent)
    return cls()

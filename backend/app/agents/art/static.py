"""Agente de arte estática — 1:1 (Instagram feed, LinkedIn)."""

from __future__ import annotations

from app.agents.art.base import ArtAgent


class StaticArtAgent(ArtAgent):
    """Gera uma imagem estática 1:1 (1080×1080 equivalente).

    Ideal para posts de feed do Instagram e LinkedIn.
    """

    art_type = "static"
    _slides_count = 1

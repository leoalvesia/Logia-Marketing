"""Agente de carrossel — 4:5 (Instagram/LinkedIn carrossel multi-slide)."""

from __future__ import annotations

from app.agents.art.base import ArtAgent


class CarouselArtAgent(ArtAgent):
    """Gera 3 slides em formato 4:5 para carrossel.

    Cada slide é uma variação do mesmo tema com perspectivas diferentes.
    """

    art_type = "carousel"
    _slides_count = 3

    def build_prompt(self, copy_text: str, channel: str) -> str:
        """Sobrescreve para adicionar contexto de slide sequencial."""
        base_prompt = super().build_prompt(copy_text, channel)
        return f"{base_prompt}, carousel slide, clean layout, consistent style series"

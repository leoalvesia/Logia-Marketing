"""Agente de thumbnail — 16:9 (YouTube, LinkedIn banner)."""

from __future__ import annotations

from app.agents.art.base import ArtAgent


class ThumbnailArtAgent(ArtAgent):
    """Gera 2 variações de thumbnail 16:9 (1280×720 equivalente).

    Ideal para YouTube thumbnail e LinkedIn banner.
    """

    art_type = "thumbnail"
    _slides_count = 2

    def build_prompt(self, copy_text: str, channel: str) -> str:
        """Sobrescreve para estilo de thumbnail impactante."""
        base_prompt = super().build_prompt(copy_text, channel)
        return (
            f"{base_prompt}, YouTube thumbnail style, "
            "dramatic lighting, eye-catching, wide angle composition"
        )

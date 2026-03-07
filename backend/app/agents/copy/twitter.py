"""Agente de copy para Twitter/X — tweet único ou thread."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.copy.base import CopyAgent, _NEVER_INVENT_CLAUSE
from app.constants import CHANNEL_LIMITS

_L = CHANNEL_LIMITS["twitter"]


class TwitterCopyAgent(CopyAgent):
    """Agente especializado em conteúdo para Twitter/X.

    Decide automaticamente entre tweet único e thread com base no volume
    de conteúdo. Cada tweet respeita o limite de caracteres da plataforma.

    Input esperado (context):
        tema, resumo, link_origem, plataformas_origem, nicho_usuario, persona_usuario

    Output garantido:
        {
            "tweets": list[str] — lista de tweets (1–5 itens, cada um ≤ 280 chars),
            "tipo":   str       — "thread" (> 1 tweet) ou "single" (1 tweet),
            "source_url": str   — sempre igual a context["link_origem"],
        }
        Em erro: {"error": str, "source_url": str}
    """

    CHANNEL = "twitter"
    MAX_TOKENS = 1024
    _CHANNEL_ACTION = "Gere conteúdo para Twitter/X no formato JSON especificado acima."

    def _system_prompt(self) -> str:
        return (
            "Você é um especialista em marketing para Twitter/X voltado ao mercado "
            f"brasileiro. Crie threads ou tweets únicos diretos, com dados e insights "
            f"concretos. {_NEVER_INVENT_CLAUSE}\n\n"
            "Formato obrigatório:\n"
            "{\n"
            '  "tweets": ["tweet 1", "tweet 2"],\n'
            '  "tipo": "thread"\n'
            "}\n\n"
            "Regras:\n"
            f"- Cada tweet: máximo {_L['tweet']} caracteres\n"
            f"- Thread: entre 2 e {_L['thread_max']} tweets; tweet único: lista com 1 item\n"
            "- tipo: 'thread' se mais de 1 tweet, 'single' se exatamente 1\n"
            "- Primeiro tweet deve ser o mais impactante (gancho)\n"
            "- Use emojis com moderação; inclua dados e fatos concretos"
        )

    def _empty_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"tweets": [], "tipo": "single"}

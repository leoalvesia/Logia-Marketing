"""Agente de copy para Instagram — captions com hashtags e gancho visual."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.copy.base import CopyAgent, _NEVER_INVENT_CLAUSE
from app.constants import CHANNEL_LIMITS

_L = CHANNEL_LIMITS["instagram"]


class InstagramCopyAgent(CopyAgent):
    """Agente especializado em captions para Instagram.

    Gera posts com storytelling, emojis estratégicos, hashtags de nicho e
    sugestão de gancho visual (imagem ou vídeo de abertura).

    Input esperado (context):
        tema, resumo, link_origem, plataformas_origem, nicho_usuario, persona_usuario

    Output garantido:
        {
            "caption":      str   — legenda (máx. CHANNEL_LIMITS["instagram"]["caption"] chars),
            "hashtags":     list  — entre hashtags_min e hashtags_max itens,
            "gancho_visual":str   — 1 frase descrevendo o visual de abertura,
            "source_url":   str   — sempre igual a context["link_origem"],
        }
        Em erro: {"error": str, "source_url": str}
    """

    CHANNEL = "instagram"
    MAX_TOKENS = 1024
    _CHANNEL_ACTION = "Gere um post completo para Instagram no formato JSON especificado acima."

    def _system_prompt(self) -> str:
        return (
            "Você é um especialista em marketing para Instagram voltado ao mercado "
            f"brasileiro. Crie captions envolventes com storytelling, emojis estratégicos "
            f"e chamadas para ação. {_NEVER_INVENT_CLAUSE}\n\n"
            "Formato obrigatório:\n"
            "{\n"
            f'  "caption": "legenda completa (máximo {_L["caption"]} caracteres, inclui emojis e CTA)",\n'
            '  "hashtags": ["#hashtag1", "#hashtag2"],\n'
            '  "gancho_visual": "descrição do vídeo ou imagem de abertura para capturar atenção"\n'
            "}\n\n"
            "Regras:\n"
            f"- caption: máximo {_L['caption']} caracteres\n"
            f"- hashtags: entre {_L['hashtags_min']} e {_L['hashtags_max']}, relevantes ao nicho\n"
            "- gancho_visual: 1 frase descrevendo o visual que acompanha o post"
        )

    def _empty_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"caption": "", "hashtags": [], "gancho_visual": ""}

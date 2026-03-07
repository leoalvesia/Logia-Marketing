"""Agente de copy para LinkedIn — texto profissional com storytelling."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.copy.base import CopyAgent, _NEVER_INVENT_CLAUSE
from app.constants import CHANNEL_LIMITS

_L = CHANNEL_LIMITS["linkedin"]


class LinkedinCopyAgent(CopyAgent):
    """Agente especializado em posts para LinkedIn B2B.

    Produz texto profissional com estrutura de storytelling: abertura
    impactante → desenvolvimento com dados → reflexão → CTA.

    Input esperado (context):
        tema, resumo, link_origem, plataformas_origem, nicho_usuario, persona_usuario

    Output garantido:
        {
            "post":            str — texto completo (máx. CHANNEL_LIMITS["linkedin"]["post"] chars),
            "abertura_gancho": str — primeira frase antes do "ver mais" (máx. 150 chars),
            "source_url":      str — sempre igual a context["link_origem"],
        }
        Em erro: {"error": str, "source_url": str}
    """

    CHANNEL = "linkedin"
    MAX_TOKENS = 1500
    _CHANNEL_ACTION = "Gere um post completo para LinkedIn no formato JSON especificado acima."

    def _system_prompt(self) -> str:
        return (
            "Você é um especialista em marketing de conteúdo para LinkedIn voltado ao "
            f"mercado B2B brasileiro. Crie posts profissionais com storytelling que geram "
            f"engajamento e credibilidade. {_NEVER_INVENT_CLAUSE}\n\n"
            "Formato obrigatório:\n"
            "{\n"
            f'  "post": "texto completo do post (máximo {_L["post"]} caracteres)",\n'
            '  "abertura_gancho": "primeira frase impactante que aparece antes do ver mais"\n'
            "}\n\n"
            "Regras:\n"
            f"- post: máximo {_L['post']} caracteres\n"
            "- Estrutura: abertura impactante → desenvolvimento com dados → reflexão → CTA\n"
            "- Linguagem profissional mas acessível, tom consultivo\n"
            f"- abertura_gancho: máximo {_L['abertura_gancho']} caracteres (aparece antes do 'ver mais')"
        )

    def _empty_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"post": "", "abertura_gancho": ""}

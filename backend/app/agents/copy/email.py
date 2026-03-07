"""Agente de copy para Email — JSON estruturado compatível com template parser."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.copy.base import CopyAgent, _NEVER_INVENT_CLAUSE
from app.constants import CHANNEL_LIMITS

_L = CHANNEL_LIMITS["email"]


class EmailCopyAgent(CopyAgent):
    """Agente especializado em email marketing para consultores B2B.

    Gera email estruturado em seções (body_sections) para facilitar o
    parsing por templates de HTML. Todos os campos respeitam limites
    definidos em CHANNEL_LIMITS["email"].

    Input esperado (context):
        tema, resumo, link_origem, plataformas_origem, nicho_usuario, persona_usuario

    Output garantido:
        {
            "subject":      str        — assunto (máx. 60 chars),
            "preview_text": str        — pré-visualização (máx. 90 chars),
            "body_sections":list[dict] — lista de {"heading": str, "content": str},
            "cta":          str        — texto do botão (máx. 40 chars),
            "source_url":   str        — sempre igual a context["link_origem"],
        }
        Em erro: {"error": str, "source_url": str}
    """

    CHANNEL = "email"
    MAX_TOKENS = 2048
    _CHANNEL_ACTION = "Gere o email completo no formato JSON estruturado especificado acima."

    def _system_prompt(self) -> str:
        return (
            "Você é um especialista em email marketing para consultores e pequenas "
            f"empresas brasileiras. Crie emails que convertem com assunto irresistível, "
            f"preview_text curto e corpo estruturado em seções. {_NEVER_INVENT_CLAUSE}\n\n"
            "Formato obrigatório:\n"
            "{\n"
            f'  "subject": "assunto do email (máximo {_L["subject"]} chars, gera curiosidade)",\n'
            f'  "preview_text": "texto de pré-visualização (máximo {_L["preview_text"]} chars)",\n'
            '  "body_sections": [\n'
            '    {"heading": "Título da seção", "content": "Parágrafo da seção"}\n'
            "  ],\n"
            f'  "cta": "texto do botão de call-to-action (máximo {_L["cta"]} chars)"\n'
            "}\n\n"
            "Regras:\n"
            f"- subject: máximo {_L['subject']} caracteres; gere curiosidade ou prometa valor\n"
            f"- preview_text: máximo {_L['preview_text']} caracteres; complementa o subject\n"
            f"- body_sections: entre {_L['sections_min']} e {_L['sections_max']} seções com heading e content\n"
            f"- cta: ação clara e direta (ex.: 'Leia o artigo completo'), máximo {_L['cta']} chars\n"
            "- Tom: pessoal, direto e orientado a valor para o leitor"
        )

    def _empty_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "subject": "",
            "preview_text": "",
            "body_sections": [],
            "cta": "",
        }

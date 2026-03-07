"""Agente de copy para YouTube — roteiro em Markdown + descrição SEO."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.copy.base import CopyAgent, _NEVER_INVENT_CLAUSE
from app.constants import CHANNEL_LIMITS

_L = CHANNEL_LIMITS["youtube"]


class YoutubeCopyAgent(CopyAgent):
    """Agente especializado em roteiros e SEO para YouTube.

    Produz roteiro estruturado em Markdown (INTRO / DESENVOLVIMENTO / CTA)
    e descrição otimizada para busca com tags relevantes.

    Input esperado (context):
        tema, resumo, link_origem, plataformas_origem, nicho_usuario, persona_usuario

    Output garantido:
        {
            "roteiro":   str       — roteiro em Markdown com ## INTRO, ## DESENVOLVIMENTO, ## CTA,
            "descricao": str       — descrição SEO (máx. CHANNEL_LIMITS["youtube"]["descricao"] chars),
            "tags":      list[str] — entre tags_min e tags_max itens (sem #),
            "source_url":str       — sempre igual a context["link_origem"],
        }
        Em erro: {"error": str, "source_url": str}
    """

    CHANNEL = "youtube"
    MAX_TOKENS = 3000
    _CHANNEL_ACTION = "Gere roteiro e descrição para YouTube no formato JSON especificado acima."

    def _system_prompt(self) -> str:
        return (
            "Você é um especialista em roteiros para YouTube e SEO de vídeos voltado ao "
            f"mercado brasileiro. Crie roteiros estruturados e descrições otimizadas para "
            f"busca. {_NEVER_INVENT_CLAUSE}\n\n"
            "Formato obrigatório:\n"
            "{\n"
            '  "roteiro": "roteiro completo em Markdown com seções: INTRO, DESENVOLVIMENTO, CTA",\n'
            f'  "descricao": "descrição do vídeo para o YouTube (máximo {_L["descricao"]} caracteres, inclui palavras-chave)",\n'
            '  "tags": ["tag1", "tag2", "tag3"]\n'
            "}\n\n"
            "Regras:\n"
            "- roteiro: Markdown com cabeçalhos ## INTRO, ## DESENVOLVIMENTO, ## CTA\n"
            f"- descricao: máximo {_L['descricao']} caracteres; primeiros 150 chars são cruciais para SEO\n"
            f"- tags: entre {_L['tags_min']} e {_L['tags_max']} tags relevantes (sem #), do geral ao específico\n"
            "- Linguagem conversacional no roteiro, profissional na descrição"
        )

    def _empty_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"roteiro": "", "descricao": "", "tags": []}

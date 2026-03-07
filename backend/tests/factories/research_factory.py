"""Factory functions para resultados de pesquisa do orquestrador.

Uso:
    from tests.factories.research_factory import create_mock_research_result

    result = create_mock_research_result("instagram")
    all_platforms = [create_mock_research_result(p) for p in
                     ["instagram", "linkedin", "youtube", "twitter"]]
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


# Dados realistas por plataforma — espelham o que o orquestrador retorna
_PLATFORM_TEMPLATES: dict[str, dict] = {
    "instagram": {
        "title": "Tendências de Reels para consultores no Instagram Q1 2026",
        "summary": (
            "Reels com menos de 30 segundos dominam o alcance orgânico no "
            "primeiro trimestre de 2026. Consultores que publicam 3x/semana "
            "reportam aumento de 40% no engajamento."
        ),
        "source_url": "https://example.com/instagram-trends-q1-2026",
        "channels": ["instagram"],
        "score": 0.85,
    },
    "linkedin": {
        "title": "IA generativa transforma processos de marketing em 2026",
        "summary": (
            "Empresas brasileiras adotam ferramentas de IA para automação de "
            "conteúdo, reduzindo em 70% o tempo de produção sem perder qualidade."
        ),
        "source_url": "https://example.com/article-ia-marketing-2026",
        "channels": ["linkedin", "youtube"],
        "score": 0.92,
    },
    "youtube": {
        "title": "Vídeos curtos vs. longa duração: o que funciona melhor em 2026?",
        "summary": (
            "Análise comparativa mostra que vídeos educativos entre 8-12 minutos "
            "têm 60% mais retenção que vídeos curtos no YouTube para nicho B2B."
        ),
        "source_url": "https://example.com/youtube-format-study-2026",
        "channels": ["youtube"],
        "score": 0.88,
    },
    "twitter": {
        "title": "Threads sobre IA dominam o engajamento no X/Twitter em 2026",
        "summary": (
            "Threads com 5-10 tweets sobre produtividade com IA recebem 3x mais "
            "engajamento que posts únicos. Formato ideal: dado + insight + CTA."
        ),
        "source_url": "https://example.com/twitter-threads-ai-2026",
        "channels": ["twitter"],
        "score": 0.80,
    },
    "email": {
        "title": "Email marketing tem maior ROI que redes sociais para consultores B2B",
        "summary": (
            "Estudo revela que consultores com lista de email própria têm ROI 42x "
            "maior que estratégias focadas exclusivamente em redes sociais."
        ),
        "source_url": "https://example.com/email-roi-b2b-2026",
        "channels": ["email"],
        "score": 0.87,
    },
}

_DEFAULT_TEMPLATE = {
    "title": "Tendência genérica de conteúdo digital em 2026",
    "summary": "Resumo de tendência para fins de teste.",
    "source_url": "https://example.com/generic-trend-2026",
    "channels": ["instagram", "linkedin"],
    "score": 0.75,
}


def create_mock_research_result(
    platform: str = "linkedin",
    n_topics: int = 1,
    rank_start: int = 1,
) -> dict:
    """
    Cria um dict no formato retornado pelo orquestrador de pesquisa.

    O formato corresponde ao que os agentes de copy esperam receber como input:
    {
        "topics": [
            {
                "id": "...",
                "title": "...",
                "summary": "...",
                "source_url": "...",
                "channels": [...],
                "score": 0.92,
                "rank": 1,
                "published_at": "2026-03-04T09:00:00Z"
            }
        ]
    }

    Args:
        platform: Plataforma de origem ('instagram', 'linkedin', 'youtube',
                  'twitter', 'email'). Define o template de dados.
        n_topics: Número de tópicos a gerar (1-10, igual ao orquestrador).
        rank_start: Rank do primeiro tópico gerado.

    Returns:
        Dict com chave 'topics' contendo lista de tópicos fake.
    """
    template = _PLATFORM_TEMPLATES.get(platform, _DEFAULT_TEMPLATE)
    published_at = "2026-03-04T09:00:00Z"

    topics = []
    for i in range(n_topics):
        score = max(0.1, template["score"] - i * 0.05)  # decai levemente por rank
        topics.append(
            {
                "id": str(uuid.uuid4()),
                "title": template["title"] if i == 0 else f"{template['title']} (variação {i + 1})",
                "summary": template["summary"],
                "source_url": template["source_url"],
                "channels": template["channels"],
                "score": round(score, 2),
                "rank": rank_start + i,
                "published_at": published_at,
            }
        )

    return {"topics": topics}


def create_mock_research_result_multi_platform(
    platforms: list[str] | None = None,
) -> dict:
    """
    Cria resultado de pesquisa com tópicos de múltiplas plataformas.
    Simula o comportamento do orquestrador quando todas as fontes retornam dados.

    Args:
        platforms: Lista de plataformas. Default: todas as 5.

    Returns:
        Dict com 'topics' contendo um tópico de cada plataforma especificada.
    """
    if platforms is None:
        platforms = ["instagram", "linkedin", "youtube", "twitter", "email"]

    all_topics = []
    for rank, platform in enumerate(platforms, start=1):
        result = create_mock_research_result(platform=platform, rank_start=rank)
        all_topics.extend(result["topics"])

    return {"topics": all_topics}

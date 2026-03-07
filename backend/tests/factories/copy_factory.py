"""Factory functions para objetos Copy.

Uso:
    from tests.factories.copy_factory import create_mock_copy

    copy = create_mock_copy("instagram", '{"caption": "Olá!"}')
    copy_with_url = create_mock_copy(
        channel="linkedin",
        content='{"text": "Post LinkedIn"}',
        source_url="https://minha-fonte.com/artigo",
    )
"""

from __future__ import annotations

import json
import uuid

from app.models.copy import Copy, CopyChannel, CopyStatus

# Conteúdos padrão por canal — realistas e adequados ao formato esperado pelos agentes
_DEFAULT_CONTENT: dict[str, dict] = {
    "instagram": {
        "caption": (
            "A IA está revolucionando o marketing de conteúdo! 🚀\n\n"
            "Empresas que adotaram ferramentas de geração automatizada reduziram "
            "em 70% o tempo de produção.\n\n"
            "#MarketingDigital #InteligenciaArtificial #ContentMarketing"
        ),
        "visual_hook": "Gráfico mostrando redução de 70% no tempo de produção",
        "source_url": "https://example.com/article-ia-marketing-2026",
    },
    "linkedin": {
        "text": (
            "A revolução silenciosa do marketing de conteúdo chegou ao Brasil.\n\n"
            "Nos últimos 6 meses, consultores e pequenas empresas que adotaram IA "
            "para produção de conteúdo relatam uma redução de 70% no tempo gasto.\n\n"
            "Fonte: example.com/article-ia-marketing-2026"
        ),
        "carousel_cover": "Slide 1: A IA que economiza 70% do seu tempo",
        "source_url": "https://example.com/article-ia-marketing-2026",
    },
    "twitter": {
        "tweets": [
            "🧵 Thread: IA no marketing de conteúdo",
            "1/ Empresas brasileiras estão economizando 70% do tempo com IA",
            "2/ Qualidade mantida — ou melhorada",
            "3/ A pergunta não é 'se', é 'quando'",
        ],
        "media_suggestion": "Screenshot do estudo com os dados de produtividade",
        "source_url": "https://example.com/article-ia-marketing-2026",
    },
    "youtube": {
        "script": (
            "INTRO: Você sabia que empresas estão economizando 70% do tempo com IA? "
            "Nesse vídeo vou te mostrar como...\n\n"
            "DESENVOLVIMENTO: Vamos explorar como ferramentas de IA estão mudando "
            "a forma como criamos conteúdo...\n\n"
            "CTA: Curta e se inscreva para mais conteúdo sobre IA e marketing!"
        ),
        "description": (
            "Nesse vídeo exploramos como a IA está transformando o marketing "
            "de conteúdo no Brasil."
        ),
        "tags": ["IA", "MarketingDigital", "ContentMarketing", "AutomaçãoDeConteúdo"],
        "thumbnail_concept": "Pessoa olhando para gráfico de crescimento com IA no fundo",
        "source_url": "https://example.com/article-ia-marketing-2026",
    },
    "email": {
        "subject": "Como a IA pode reduzir 70% do seu tempo de criação de conteúdo",
        "intro": "Olá! Trouxemos um estudo incrível sobre IA e marketing.",
        "body": (
            "Empresas brasileiras estão usando IA para transformar seus processos "
            "de marketing. Confira os resultados impressionantes."
        ),
        "cta": "Leia o artigo completo",
        "source_url": "https://example.com/article-ia-marketing-2026",
    },
}

DEFAULT_SOURCE_URL = "https://example.com/article-ia-marketing-2026"


def create_mock_copy(
    channel: str = "instagram",
    content: str | None = None,
    source_url: str = DEFAULT_SOURCE_URL,
    pipeline_id: str | None = None,
    status: CopyStatus = CopyStatus.DRAFT,
) -> Copy:
    """
    Cria um objeto Copy em memória (não persiste no banco).

    Args:
        channel: Canal alvo ('instagram', 'linkedin', 'twitter', 'youtube', 'email').
        content: String JSON com o conteúdo. Se None, usa o default do canal.
        source_url: URL de origem do conteúdo (obrigatório no domínio).
        pipeline_id: ID do pipeline associado. Gera UUID aleatório se None.
        status: Status inicial da copy (default: DRAFT).

    Returns:
        Objeto Copy pronto para ser adicionado à sessão ou usado em asserts.
    """
    channel_enum = CopyChannel(channel)

    if content is None:
        content = json.dumps(
            _DEFAULT_CONTENT.get(
                channel,
                {"content": f"Conteúdo de teste para {channel}"},
            ),
            ensure_ascii=False,
        )

    return Copy(
        id=str(uuid.uuid4()),
        pipeline_id=pipeline_id or str(uuid.uuid4()),
        channel=channel_enum,
        content=content,
        source_url=source_url,
        status=status,
    )

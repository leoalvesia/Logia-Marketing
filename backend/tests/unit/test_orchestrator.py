"""Testes unitários do orquestrador de pesquisa."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.agents.research.orchestrator import (
    _calc_recencia,
    _extract_resumo,
    _group_by_theme,
    _parse_date,
    _verify_url,
    orchestrate,
)

# ── Fixture global: desabilita requisições HTTP reais em todos os testes ──────
# Todos os testes assumem URLs válidas por padrão; testes específicos sobrescrevem.


@pytest.fixture(autouse=True)
def mock_verify_url_always_true():
    """Patcha _verify_url para retornar True em todos os testes.

    Evita requisições HTTP reais nos testes unitários.
    Testes de verificação de URL sobrescrevem com side_effect próprio.
    """
    with patch(
        "app.agents.research.orchestrator._verify_url",
        return_value=True,
    ):
        yield


# ── Fixture de dados brutos ───────────────────────────────────────────────────

_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load_raw_results() -> list[dict]:
    path = _FIXTURES_DIR / "mock_raw_collector_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _with_mocked_nicho(nicho_score: float = 0.7):
    """Decorator-like context: patcha _score_nicho_relevance retornando valor fixo."""
    return patch(
        "app.agents.research.orchestrator._score_nicho_relevance",
        return_value=nicho_score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Testes de contratos principais (com fixture real)
# ══════════════════════════════════════════════════════════════════════════════


class TestOrchestrateContracts:
    """Verifica os contratos de output do orquestrador."""

    def test_retorna_top_10(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital para consultores")
        assert len(result) == 10

    def test_ordenado_por_score_decrescente(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        assert result[0]["score"] >= result[4]["score"] >= result[9]["score"]
        assert result[0]["score"] > result[9]["score"]

    def test_todos_tem_link_origem_nao_nulo(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result:
            assert item.get("link_origem"), f"item sem link_origem: {item.get('titulo')}"

    def test_schema_completo_de_cada_item(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        required_keys = {
            "titulo",
            "resumo",
            "link_origem",
            "plataformas",
            "score",
            "publicado_em",
            "source_verified",
            "dados_pesquisa",
        }
        for item in result:
            assert required_keys.issubset(
                item.keys()
            ), f"chaves faltando: {required_keys - item.keys()}"

    def test_score_entre_0_e_1(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result:
            assert 0.0 <= item["score"] <= 1.0, f"score inválido: {item['score']}"

    def test_plataformas_e_lista_nao_vazia(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result:
            assert isinstance(item["plataformas"], list)
            assert len(item["plataformas"]) >= 1

    def test_link_origem_comeca_com_https(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result:
            assert item["link_origem"].startswith(
                "https://"
            ), f"URL inválida: {item['link_origem']}"

    def test_top5_tem_link_origem(self):
        """Regra crítica: os 5 primeiros nunca devem ter link_origem vazio."""
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result[:5]:
            assert item["link_origem"], "Top 5 contém item sem fonte verificável"


# ══════════════════════════════════════════════════════════════════════════════
# Regra crítica: item sem link_origem → score = 0
# ══════════════════════════════════════════════════════════════════════════════


class TestLinkOrigemCritico:
    def test_item_sem_url_recebe_score_zero(self):
        raw = [
            {
                "title": "Tema sem fonte",
                "description": "Conteúdo sem URL verificável.",
                "url": "",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "instagram",
            },
            {
                "title": "Outro tema sem URL",
                "description": "Mais conteúdo sem fonte.",
                "url": "",
                "published_at": "2026-03-06T09:00:00Z",
                "platform": "linkedin",
            },
        ]
        with _with_mocked_nicho(0.9):
            result = orchestrate(raw, "marketing")
        for item in result:
            assert item["score"] == 0.0

    def test_item_sem_url_vai_para_o_fim(self):
        """Tema com URL deve aparecer antes de tema sem URL."""
        raw = [
            {
                "title": "Tema sem fonte alguma",
                "description": "Conteúdo inventado.",
                "url": "",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "instagram",
            },
            {
                "title": "Tema com fonte verificável",
                "description": "Conteúdo com origem real.",
                "url": "https://example.com/fonte-real",
                "published_at": "2026-03-06T09:00:00Z",
                "platform": "linkedin",
            },
        ]
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing")
        # O item com URL deve vir antes do sem URL
        urls = [item["link_origem"] for item in result]
        idx_com_url = next(i for i, u in enumerate(urls) if u)
        idx_sem_url = next(i for i, u in enumerate(urls) if not u)
        assert idx_com_url < idx_sem_url


# ══════════════════════════════════════════════════════════════════════════════
# Cálculo de score
# ══════════════════════════════════════════════════════════════════════════════


class TestScoreCalculation:
    def test_multiplos_canais_aumentam_score(self):
        """Tema presente em mais canais deve ter score maior."""
        raw = [
            # "ChatGPT automação" → linkedin + youtube + instagram (3 canais)
            {
                "title": "ChatGPT automação de propostas comerciais",
                "description": "Automatize propostas com ChatGPT e ganhe horas por dia.",
                "url": "https://example.com/chatgpt-propostas-linkedin",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "linkedin",
            },
            {
                "title": "ChatGPT automação de propostas comerciais",
                "description": "Automatize propostas com ChatGPT e ganhe horas por dia.",
                "url": "https://example.com/chatgpt-propostas-youtube",
                "published_at": "2026-03-06T09:00:00Z",
                "platform": "youtube",
            },
            {
                "title": "ChatGPT automação de propostas comerciais",
                "description": "Automatize propostas com ChatGPT e ganhe horas por dia.",
                "url": "https://example.com/chatgpt-propostas-instagram",
                "published_at": "2026-03-06T08:00:00Z",
                "platform": "instagram",
            },
            # "Podcast jurídico crescimento" → twitter apenas (1 canal)
            {
                "title": "Podcast nicho jurídico crescimento audiência",
                "description": "Como advogados estão crescendo audiência via podcast.",
                "url": "https://example.com/podcast-juridico",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "twitter",
            },
        ]
        with _with_mocked_nicho(0.5):
            result = orchestrate(raw, "marketing")
        tema_multicanal = next(r for r in result if "ChatGPT" in r["titulo"])
        tema_unico = next(r for r in result if "Podcast" in r["titulo"])
        assert tema_multicanal["score"] > tema_unico["score"]

    def test_recencia_aumenta_score(self):
        """Tema recente deve ter score maior que tema antigo (mesma plataforma)."""
        raw = [
            {
                "title": "Tendências de inteligência artificial no marketing digital",
                "description": "IA está redefinindo o marketing em 2026.",
                "url": "https://example.com/ia-tendencias-2026",
                "published_at": "2026-03-06T10:00:00Z",  # hoje — recente
                "platform": "linkedin",
            },
            {
                "title": "Estratégias de podcast para crescimento B2B corporativo",
                "description": "Podcasts B2B crescem 80% e atraem clientes qualificados.",
                "url": "https://example.com/podcast-b2b-estrategia",
                "published_at": "2025-01-01T10:00:00Z",  # mais de um ano atrás
                "platform": "linkedin",
            },
        ]
        with _with_mocked_nicho(0.5):
            result = orchestrate(raw, "marketing")
        recente = next(r for r in result if "inteligência artificial" in r["titulo"])
        antigo = next(r for r in result if "podcast" in r["titulo"].lower())
        assert recente["score"] > antigo["score"]

    def test_nicho_relevante_aumenta_score(self):
        """Score mais alto de nicho deve gerar score final maior."""
        raw = [
            {
                "title": "Automação de marketing com ferramentas de inteligência artificial",
                "description": "Ferramentas de IA automatizam 60% das tarefas de marketing.",
                "url": "https://example.com/automacao-ia-marketing",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "linkedin",
            },
            {
                "title": "Crescimento orgânico no TikTok para empresas de moda feminina",
                "description": "Estratégias de TikTok para marcas de moda crescerem organicamente.",
                "url": "https://example.com/tiktok-moda-feminina",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "instagram",
            },
        ]
        with patch(
            "app.agents.research.orchestrator._score_nicho_relevance",
            side_effect=[0.9, 0.1],  # automacao=0.9, tiktok-moda=0.1
        ):
            result = orchestrate(raw, "marketing digital B2B")
        tema_relevante = next(r for r in result if "Automação" in r["titulo"])
        tema_irrelevante = next(r for r in result if "TikTok" in r["titulo"])
        assert tema_relevante["score"] > tema_irrelevante["score"]


# ══════════════════════════════════════════════════════════════════════════════
# Agrupamento por similaridade
# ══════════════════════════════════════════════════════════════════════════════


class TestGrouping:
    def test_titulos_similares_agrupados(self):
        items = [
            {
                "title": "IA generativa transforma marketing",
                "description": "Desc",
                "url": "https://x.com/a",
                "published_at": "2026-03-05",
                "platform": "linkedin",
            },
            {
                "title": "IA generativa está mudando o marketing digital",
                "description": "Desc",
                "url": "https://x.com/b",
                "published_at": "2026-03-05",
                "platform": "youtube",
            },
        ]
        groups = _group_by_theme(items)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_titulos_distintos_nao_agrupados(self):
        items = [
            {
                "title": "Email marketing B2B ROI",
                "description": "Desc",
                "url": "https://x.com/a",
                "published_at": "2026-03-05",
                "platform": "linkedin",
            },
            {
                "title": "Podcast crescimento consultores",
                "description": "Desc",
                "url": "https://x.com/b",
                "published_at": "2026-03-05",
                "platform": "youtube",
            },
            {
                "title": "TikTok para negócios B2B",
                "description": "Desc",
                "url": "https://x.com/c",
                "published_at": "2026-03-05",
                "platform": "instagram",
            },
        ]
        groups = _group_by_theme(items)
        assert len(groups) == 3

    def test_grupo_consolida_plataformas(self):
        raw = [
            {
                "title": "Tema idêntico",
                "description": "Desc.",
                "url": "https://x.com/1",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "linkedin",
            },
            {
                "title": "Tema idêntico",
                "description": "Desc.",
                "url": "https://x.com/2",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "youtube",
            },
            {
                "title": "Tema idêntico",
                "description": "Desc.",
                "url": "https://x.com/3",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "instagram",
            },
        ]
        with _with_mocked_nicho(0.5):
            result = orchestrate(raw, "marketing")
        assert len(result) == 1
        assert set(result[0]["plataformas"]) == {"linkedin", "youtube", "instagram"}


# ══════════════════════════════════════════════════════════════════════════════
# Cálculo de recência (unit)
# ══════════════════════════════════════════════════════════════════════════════


class TestCalcRecencia:
    def test_menos_de_48h_retorna_1(self):
        from datetime import timedelta

        recent = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        assert _calc_recencia(recent) == 1.0

    def test_entre_48h_e_7d_retorna_0_6(self):
        from datetime import timedelta

        three_days_ago = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        assert _calc_recencia(three_days_ago) == 0.6

    def test_mais_antigo_retorna_0_2(self):
        assert _calc_recencia("2025-01-01T00:00:00Z") == 0.2

    def test_data_invalida_retorna_0_2(self):
        assert _calc_recencia("not-a-date") == 0.2
        assert _calc_recencia("") == 0.2
        assert _calc_recencia("1234567890") == 0.2

    def test_formato_z_aceito(self):
        from datetime import timedelta

        recent = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert _calc_recencia(recent) == 1.0


# ══════════════════════════════════════════════════════════════════════════════
# Extração de resumo
# ══════════════════════════════════════════════════════════════════════════════


class TestExtractResumo:
    def test_limita_a_3_frases(self):
        text = "Frase um. Frase dois. Frase três. Frase quatro. Frase cinco."
        result = _extract_resumo(text)
        assert result.count(". ") <= 2  # no máximo 2 pontos separadores

    def test_descricao_vazia_retorna_vazio(self):
        assert _extract_resumo("") == ""

    def test_nao_inventa_conteudo(self):
        original = "Empresas adotam IA. Produtividade cresce 70%."
        result = _extract_resumo(original)
        # Todo conteúdo do resumo deve vir do original
        for sentence in result.rstrip(".").split("."):
            if sentence.strip():
                assert sentence.strip() in original


# ══════════════════════════════════════════════════════════════════════════════
# Casos de borda
# ══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_entrada_vazia_retorna_lista_vazia(self):
        assert orchestrate([], "marketing") == []

    def test_menos_de_10_grupos_retorna_tudo(self):
        raw = [
            {
                "title": "Email marketing ROI superior redes sociais B2B",
                "description": "Email tem ROI 42x maior que social para B2B.",
                "url": "https://example.com/email-roi",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "linkedin",
            },
            {
                "title": "Podcast crescimento audiência jurídico nicho",
                "description": "Advogados usam podcasts para captar clientes.",
                "url": "https://example.com/podcast-juridico",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "youtube",
            },
            {
                "title": "TikTok empresarial marcas brasileiras crescimento",
                "description": "Empresas brasileiras crescem no TikTok.",
                "url": "https://example.com/tiktok-empresarial",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "instagram",
            },
            {
                "title": "LinkedIn algoritmo alcance orgânico novidades 2026",
                "description": "Novo algoritmo do LinkedIn prioriza nicho.",
                "url": "https://example.com/linkedin-algoritmo",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "twitter",
            },
            {
                "title": "WhatsApp Business automação captação leads consultores",
                "description": "Automação de WhatsApp aumenta 50% as conversões.",
                "url": "https://example.com/whatsapp-automacao",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "linkedin",
            },
        ]
        with _with_mocked_nicho(0.5):
            result = orchestrate(raw, "marketing")
        assert len(result) == 5

    def test_sem_api_key_ainda_funciona(self):
        """Sem ANTHROPIC_API_KEY o orchestrador usa fallback 0.5 e não explode."""
        raw = [
            {
                "title": "Tema de teste",
                "description": "Desc.",
                "url": "https://example.com/teste",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "linkedin",
            }
        ]
        with patch("app.agents.research.orchestrator.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            result = orchestrate(raw, "marketing")
        assert len(result) == 1
        assert result[0]["score"] > 0

    def test_item_sem_platform_tratado(self):
        raw = [
            {
                "title": "Tema sem plataforma",
                "description": "Desc.",
                "url": "https://example.com/sem-plataforma",
                "published_at": "2026-03-05T10:00:00Z",
                "platform": "",
            }
        ]
        with _with_mocked_nicho(0.5):
            result = orchestrate(raw, "marketing")
        assert isinstance(result, list)

    def test_resultado_e_lista_de_dicts(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)


# ══════════════════════════════════════════════════════════════════════════════
# Extração de dados numéricos (dados_pesquisa)
# ══════════════════════════════════════════════════════════════════════════════


from app.agents.research.orchestrator import _extract_statistics


class TestExtractStatistics:
    def test_extrai_percentual(self):
        text = "Empresas reduziram 70% do tempo de produção com IA."
        assert "70%" in _extract_statistics(text)

    def test_extrai_multiplicador_x(self):
        text = "Crescimento de 3x em 6 meses após adoção da ferramenta."
        result = _extract_statistics(text)
        assert "3x" in result or "3X" in result.upper()

    def test_extrai_valor_real(self):
        text = "Economia média de R$ 15.000 por trimestre para PMEs."
        assert "R$" in _extract_statistics(text)

    def test_descricao_sem_numeros_retorna_vazio(self):
        text = "Conteúdo de qualidade é fundamental para engajamento no LinkedIn."
        assert _extract_statistics(text) == ""

    def test_descricao_vazia_retorna_vazio(self):
        assert _extract_statistics("") == ""

    def test_limita_a_3_frases(self):
        text = (
            "Cresceu 100%. "
            "Reduziu 50% dos custos. "
            "ROI de 200% em 3 meses. "
            "Mais 40% de leads qualificados. "
        )
        result = _extract_statistics(text)
        assert result.count("%") <= 3

    def test_todos_itens_tem_campo_dados_pesquisa(self):
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result:
            assert "dados_pesquisa" in item
            assert isinstance(item["dados_pesquisa"], str)


# ══════════════════════════════════════════════════════════════════════════════
# Verificação de source_verified
# ══════════════════════════════════════════════════════════════════════════════


class TestSourceVerification:
    """Testa a presença e semântica do campo source_verified."""

    def test_url_valida_marca_source_verified_true(self):
        """Quando _verify_url retorna True, source_verified deve ser True."""
        raw = [
            {
                "title": "Tema com URL válida",
                "description": "Conteúdo real.",
                "url": "https://example.com/valida",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "linkedin",
            }
        ]
        # autouse fixture já patchou _verify_url=True
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing")
        assert result[0]["source_verified"] is True

    def test_url_404_marca_source_verified_false(self):
        """Quando _verify_url retorna False (ex: 404), source_verified é False."""
        raw = [
            {
                "title": "Tema com URL morta",
                "description": "Conteúdo real mas URL expirada.",
                "url": "https://fgv.br/pesquisa/ia-pme-brasil-2026",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "instagram",
            }
        ]
        with (
            _with_mocked_nicho(0.7),
            patch(
                "app.agents.research.orchestrator._verify_url",
                return_value=False,
            ),
        ):
            result = orchestrate(raw, "marketing")
        assert result[0]["source_verified"] is False

    def test_url_morta_aplica_penalidade_de_score(self):
        """URL não verificável deve reduzir o score em 50%."""
        raw = [
            {
                "title": "Automação de email marketing para empresas B2B",
                "description": "Sequências automatizadas aumentam conversão.",
                "url": "https://example.com/email-automacao-b2b",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "linkedin",
            },
            {
                "title": "TikTok orgânico crescimento marcas moda feminina",
                "description": "Estratégias virais de curto prazo para varejo.",
                "url": "https://exemplo-morto.com/tiktok-moda",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "instagram",
            },
        ]
        with (
            _with_mocked_nicho(0.7),
            patch(
                "app.agents.research.orchestrator._verify_url",
                side_effect=lambda url: "morto" not in url,
            ),
        ):
            result = orchestrate(raw, "marketing")

        item_valido = next(r for r in result if "email" in r["titulo"].lower())
        item_morto = next(r for r in result if "TikTok" in r["titulo"])
        # Item com URL morta deve ter score menor que item com URL válida
        assert item_morto["score"] < item_valido["score"]
        assert item_morto["source_verified"] is False

    def test_url_vazia_sem_source_verified(self):
        """Item sem URL deve ter source_verified = False."""
        raw = [
            {
                "title": "Tema sem URL alguma",
                "description": "Conteúdo sem fonte.",
                "url": "",
                "published_at": "2026-03-06T10:00:00Z",
                "platform": "twitter",
            }
        ]
        with _with_mocked_nicho(0.5):
            result = orchestrate(raw, "marketing")
        assert result[0]["source_verified"] is False

    def test_todos_items_tem_campo_source_verified(self):
        """source_verified deve estar presente em todos os itens retornados."""
        raw = _load_raw_results()
        with _with_mocked_nicho(0.7):
            result = orchestrate(raw, "marketing digital")
        for item in result:
            assert "source_verified" in item, f"source_verified ausente em: {item.get('titulo')}"
            assert isinstance(item["source_verified"], bool)

    def test_verify_url_rejeita_url_sem_schema(self):
        """_verify_url retorna False para URLs sem http/https."""
        # Sobrescreve o autouse para testar a função real
        with patch("app.agents.research.orchestrator._verify_url", wraps=_verify_url):
            # URLs sem schema devem retornar False imediatamente (sem request)
            assert _verify_url("fgv.br/pesquisa") is False
            assert _verify_url("") is False
            assert _verify_url("ftp://nao-suportado.com") is False


# importar datetime e timezone para uso nos testes
from datetime import datetime, timezone

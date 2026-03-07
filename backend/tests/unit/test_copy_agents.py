"""Testes unitários dos agentes de copy (Claude mockado)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# ── Contexto padrão de teste ──────────────────────────────────────────────────

_CTX = {
    "tema": "IA generativa transforma marketing de conteúdo em 2026",
    "resumo": (
        "Empresas brasileiras reduzem 70% do tempo de produção com IA, "
        "mantendo qualidade e aumentando volume de conteúdo."
    ),
    "link_origem": "https://example.com/ia-marketing-2026",
    "plataformas_origem": ["linkedin", "youtube"],
    "nicho_usuario": "marketing digital para consultores",
    "persona_usuario": "consultores de marketing B2B",
}


def _mock_anthropic(json_payload: dict):
    """Cria mock do Anthropic client que retorna json_payload como texto."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(json_payload, ensure_ascii=False))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def _mock_anthropic_raw(text: str):
    """Cria mock que retorna texto bruto (para testar parse de markdown)."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


# ══════════════════════════════════════════════════════════════════════════════
# Base: regra crítica source_url
# ══════════════════════════════════════════════════════════════════════════════


class TestCopyAgentBase:
    def test_source_url_sempre_do_contexto(self):
        """Claude pode retornar qualquer URL — source_url DEVE ser link_origem."""
        from app.agents.copy.instagram import InstagramCopyAgent

        payload = {
            "caption": "Post teste",
            "hashtags": ["#ia", "#marketing"],
            "gancho_visual": "Visual teste",
            "source_url": "https://url-inventada-pelo-llm.com",  # deve ser ignorada
        }
        mock_client = _mock_anthropic(payload)
        with patch("app.agents.copy.base.Anthropic", return_value=mock_client):
            result = InstagramCopyAgent().generate(_CTX)

        assert result["source_url"] == _CTX["link_origem"]
        assert result["source_url"] != "https://url-inventada-pelo-llm.com"

    def test_source_url_presente_mesmo_em_erro(self):
        """Mesmo quando Claude falha, source_url deve estar no output."""
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=RuntimeError("API offline"),
        ):
            result = InstagramCopyAgent().generate(_CTX)

        assert result["source_url"] == _CTX["link_origem"]

    def test_parse_json_com_markdown_codeblock(self):
        """Deve extrair JSON mesmo que Claude envolva em ```json ... ```."""
        from app.agents.copy.base import CopyAgent

        payload = {"key": "value"}
        wrapped = f"```json\n{json.dumps(payload)}\n```"
        assert CopyAgent._parse_json(wrapped) == payload

    def test_parse_json_com_codeblock_sem_tipo(self):
        from app.agents.copy.base import CopyAgent

        payload = {"key": "value"}
        wrapped = f"```\n{json.dumps(payload)}\n```"
        assert CopyAgent._parse_json(wrapped) == payload

    def test_parse_json_direto(self):
        from app.agents.copy.base import CopyAgent

        payload = {"key": "value", "num": 42}
        assert CopyAgent._parse_json(json.dumps(payload)) == payload


# ══════════════════════════════════════════════════════════════════════════════
# Instagram
# ══════════════════════════════════════════════════════════════════════════════


class TestInstagramCopyAgent:
    _VALID_PAYLOAD = {
        "caption": "A IA está revolucionando o marketing! 🚀\n\nEmpresas reduzem 70% do tempo.",
        "hashtags": ["#MarketingDigital", "#IA", "#Consultoria", "#Conteudo", "#B2B"],
        "gancho_visual": "Gráfico animado mostrando queda de 70% no tempo de produção",
    }

    def test_schema_completo(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = InstagramCopyAgent().generate(_CTX)

        assert "caption" in result
        assert "hashtags" in result
        assert "gancho_visual" in result
        assert "source_url" in result

    def test_hashtags_e_lista(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = InstagramCopyAgent().generate(_CTX)

        assert isinstance(result["hashtags"], list)
        assert len(result["hashtags"]) >= 1

    def test_caption_nao_vazia(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = InstagramCopyAgent().generate(_CTX)

        assert len(result["caption"]) > 0

    def test_caption_respeita_limite_2200(self):
        """Caption longa gerada pelo LLM deve ser aceita se <= 2200 chars."""
        from app.agents.copy.instagram import InstagramCopyAgent

        payload = {**self._VALID_PAYLOAD, "caption": "A" * 2200}
        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(payload),
        ):
            result = InstagramCopyAgent().generate(_CTX)

        assert len(result["caption"]) <= 2200

    def test_output_em_erro_tem_error_e_source_url(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=Exception("timeout"),
        ):
            result = InstagramCopyAgent().generate(_CTX)

        assert result["source_url"] == _CTX["link_origem"]
        assert "error" in result
        assert "timeout" in result["error"]


# ══════════════════════════════════════════════════════════════════════════════
# LinkedIn
# ══════════════════════════════════════════════════════════════════════════════


class TestLinkedinCopyAgent:
    _VALID_PAYLOAD = {
        "post": (
            "A revolução silenciosa do marketing chegou ao Brasil.\n\n"
            "Consultores que adotaram IA reduzem 70% do tempo de produção "
            "mantendo qualidade. Isso muda tudo.\n\nFonte verificada."
        ),
        "abertura_gancho": "A IA está roubando horas do seu dia — e você ainda não sabe.",
    }

    def test_schema_completo(self):
        from app.agents.copy.linkedin import LinkedinCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = LinkedinCopyAgent().generate(_CTX)

        assert "post" in result
        assert "abertura_gancho" in result
        assert "source_url" in result

    def test_post_nao_vazio(self):
        from app.agents.copy.linkedin import LinkedinCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = LinkedinCopyAgent().generate(_CTX)

        assert len(result["post"]) > 0

    def test_output_em_erro_tem_error_e_source_url(self):
        from app.agents.copy.linkedin import LinkedinCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=Exception("timeout"),
        ):
            result = LinkedinCopyAgent().generate(_CTX)

        assert "error" in result
        assert result["source_url"] == _CTX["link_origem"]


# ══════════════════════════════════════════════════════════════════════════════
# Twitter
# ══════════════════════════════════════════════════════════════════════════════


class TestTwitterCopyAgent:
    _VALID_THREAD = {
        "tweets": [
            "🧵 IA no marketing: o que ninguém te conta (thread) →",
            "1/ Empresas brasileiras reduzem 70% do tempo de produção com IA.",
            "2/ A qualidade não cai — em muitos casos, melhora.",
            "3/ A pergunta não é 'se' — é 'quando'. Você já está usando?",
        ],
        "tipo": "thread",
    }
    _VALID_SINGLE = {
        "tweets": ["IA reduz 70% do tempo de produção de marketing. Você já usa?"],
        "tipo": "single",
    }

    def test_schema_completo_thread(self):
        from app.agents.copy.twitter import TwitterCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_THREAD),
        ):
            result = TwitterCopyAgent().generate(_CTX)

        assert "tweets" in result
        assert "tipo" in result
        assert "source_url" in result

    def test_tweets_e_lista(self):
        from app.agents.copy.twitter import TwitterCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_THREAD),
        ):
            result = TwitterCopyAgent().generate(_CTX)

        assert isinstance(result["tweets"], list)
        assert len(result["tweets"]) >= 1

    def test_cada_tweet_max_280_chars(self):
        from app.agents.copy.twitter import TwitterCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_THREAD),
        ):
            result = TwitterCopyAgent().generate(_CTX)

        for tweet in result["tweets"]:
            assert len(tweet) <= 280, f"Tweet com {len(tweet)} chars: {tweet[:50]}"

    def test_thread_max_5_tweets(self):
        from app.agents.copy.twitter import TwitterCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_THREAD),
        ):
            result = TwitterCopyAgent().generate(_CTX)

        assert len(result["tweets"]) <= 5

    def test_tipo_single_com_1_tweet(self):
        from app.agents.copy.twitter import TwitterCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_SINGLE),
        ):
            result = TwitterCopyAgent().generate(_CTX)

        assert result["tipo"] == "single"
        assert len(result["tweets"]) == 1

    def test_output_em_erro_tem_error_e_source_url(self):
        from app.agents.copy.twitter import TwitterCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=Exception("timeout"),
        ):
            result = TwitterCopyAgent().generate(_CTX)

        assert "error" in result
        assert result["source_url"] == _CTX["link_origem"]


# ══════════════════════════════════════════════════════════════════════════════
# YouTube
# ══════════════════════════════════════════════════════════════════════════════


class TestYoutubeCopyAgent:
    _VALID_PAYLOAD = {
        "roteiro": (
            "## INTRO\nVocê sabia que IA reduz 70% do tempo de produção?\n\n"
            "## DESENVOLVIMENTO\nVamos explorar como ferramentas de IA...\n\n"
            "## CTA\nCurta e se inscreva!"
        ),
        "descricao": (
            "Nesse vídeo, exploramos como a IA está transformando o marketing "
            "de conteúdo no Brasil. Fonte: example.com/ia-marketing-2026"
        ),
        "tags": ["IA", "MarketingDigital", "Consultoria", "ContentMarketing", "Automacao"],
    }

    def test_schema_completo(self):
        from app.agents.copy.youtube import YoutubeCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = YoutubeCopyAgent().generate(_CTX)

        assert "roteiro" in result
        assert "descricao" in result
        assert "tags" in result
        assert "source_url" in result

    def test_tags_e_lista(self):
        from app.agents.copy.youtube import YoutubeCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = YoutubeCopyAgent().generate(_CTX)

        assert isinstance(result["tags"], list)
        assert len(result["tags"]) >= 1

    def test_roteiro_contem_markdown(self):
        from app.agents.copy.youtube import YoutubeCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = YoutubeCopyAgent().generate(_CTX)

        assert "##" in result["roteiro"]

    def test_output_em_erro_tem_error_e_source_url(self):
        from app.agents.copy.youtube import YoutubeCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=Exception("timeout"),
        ):
            result = YoutubeCopyAgent().generate(_CTX)

        assert "error" in result
        assert result["source_url"] == _CTX["link_origem"]


# ══════════════════════════════════════════════════════════════════════════════
# Email
# ══════════════════════════════════════════════════════════════════════════════


class TestEmailCopyAgent:
    _VALID_PAYLOAD = {
        "subject": "Como a IA pode liberar 70% do seu tempo de marketing",
        "preview_text": "Estudo revela impacto real da IA na produtividade de consultores",
        "body_sections": [
            {
                "heading": "O problema que você conhece bem",
                "content": "Criar conteúdo de qualidade consome horas preciosas.",
            },
            {
                "heading": "O que os dados mostram",
                "content": "Empresas que adotaram IA reduziram 70% do tempo.",
            },
        ],
        "cta": "Leia o artigo completo",
    }

    def test_schema_completo(self):
        from app.agents.copy.email import EmailCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = EmailCopyAgent().generate(_CTX)

        assert "subject" in result
        assert "preview_text" in result
        assert "body_sections" in result
        assert "cta" in result
        assert "source_url" in result

    def test_body_sections_e_lista_de_dicts(self):
        from app.agents.copy.email import EmailCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = EmailCopyAgent().generate(_CTX)

        assert isinstance(result["body_sections"], list)
        for section in result["body_sections"]:
            assert "heading" in section
            assert "content" in section

    def test_subject_nao_vazio(self):
        from app.agents.copy.email import EmailCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic(self._VALID_PAYLOAD),
        ):
            result = EmailCopyAgent().generate(_CTX)

        assert len(result["subject"]) > 0

    def test_output_em_erro_tem_error_e_source_url(self):
        from app.agents.copy.email import EmailCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=Exception("timeout"),
        ):
            result = EmailCopyAgent().generate(_CTX)

        assert "error" in result
        assert result["source_url"] == _CTX["link_origem"]


# ══════════════════════════════════════════════════════════════════════════════
# Registry (get_agent)
# ══════════════════════════════════════════════════════════════════════════════


class TestConstants:
    """Verifica que CHANNEL_LIMITS está completo e é usado nos prompts."""

    def test_todos_canais_presentes(self):
        from app.constants import CHANNEL_LIMITS

        assert set(CHANNEL_LIMITS.keys()) == {
            "instagram", "linkedin", "twitter", "youtube", "email"
        }

    def test_limites_numericos_positivos(self):
        from app.constants import CHANNEL_LIMITS

        for channel, limits in CHANNEL_LIMITS.items():
            for key, val in limits.items():
                assert isinstance(val, int) and val > 0, (
                    f"{channel}.{key} = {val} deve ser int > 0"
                )

    def test_limites_refletidos_nos_prompts(self):
        """Os limites do Twitter devem aparecer no system_prompt do TwitterCopyAgent."""
        from app.agents.copy.twitter import TwitterCopyAgent
        from app.constants import CHANNEL_LIMITS

        prompt = TwitterCopyAgent()._system_prompt()
        assert str(CHANNEL_LIMITS["twitter"]["tweet"]) in prompt
        assert str(CHANNEL_LIMITS["twitter"]["thread_max"]) in prompt

    def test_never_invent_clause_em_todos_prompts(self):
        from app.agents.copy.base import _NEVER_INVENT_CLAUSE
        from app.agents.copy.instagram import InstagramCopyAgent
        from app.agents.copy.linkedin import LinkedinCopyAgent
        from app.agents.copy.twitter import TwitterCopyAgent
        from app.agents.copy.youtube import YoutubeCopyAgent
        from app.agents.copy.email import EmailCopyAgent

        agents = [
            InstagramCopyAgent(), LinkedinCopyAgent(), TwitterCopyAgent(),
            YoutubeCopyAgent(), EmailCopyAgent(),
        ]
        for agent in agents:
            prompt = agent._system_prompt()
            assert "NUNCA invente dados" in prompt, (
                f"{agent.CHANNEL}: _NEVER_INVENT_CLAUSE ausente no system_prompt"
            )

    def test_channel_action_usado_no_user_prompt(self):
        """_CHANNEL_ACTION de cada agente deve aparecer no user_prompt gerado."""
        from app.agents.copy.instagram import InstagramCopyAgent
        from app.agents.copy.linkedin import LinkedinCopyAgent

        for AgentCls in (InstagramCopyAgent, LinkedinCopyAgent):
            agent = AgentCls()
            prompt = agent._user_prompt(_CTX)
            assert agent._CHANNEL_ACTION in prompt


# ══════════════════════════════════════════════════════════════════════════════
# generate_streaming
# ══════════════════════════════════════════════════════════════════════════════


def _mock_anthropic_streaming(chunks: list[str]):
    """Cria mock do Anthropic client com streaming."""
    mock_stream = MagicMock()
    mock_stream.text_stream = iter(chunks)
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)

    mock_client = MagicMock()
    mock_client.messages.stream.return_value = mock_stream
    return mock_client


class TestGenerateStreaming:
    _CHUNKS = [
        '{"caption": "IA no marketing! ',
        '🚀", "hashtags": ["#ia"], "gancho_visual": "gráfico"}',
    ]

    def test_chunks_recebidos_via_callback(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        received = []
        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic_streaming(self._CHUNKS),
        ):
            InstagramCopyAgent().generate_streaming(_CTX, on_chunk=received.append)

        assert received == self._CHUNKS

    def test_resultado_final_contem_source_url(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic_streaming(self._CHUNKS),
        ):
            result = InstagramCopyAgent().generate_streaming(_CTX)

        assert result["source_url"] == _CTX["link_origem"]

    def test_json_montado_dos_chunks(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic_streaming(self._CHUNKS),
        ):
            result = InstagramCopyAgent().generate_streaming(_CTX)

        assert "caption" in result
        assert "hashtags" in result

    def test_erro_na_api_retorna_error_e_source_url(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            side_effect=RuntimeError("stream offline"),
        ):
            result = InstagramCopyAgent().generate_streaming(_CTX)

        assert "error" in result
        assert result["source_url"] == _CTX["link_origem"]

    def test_chunk_callback_erro_nao_aborta_geracao(self):
        """Exceção no on_chunk não deve abortar a geração."""
        from app.agents.copy.instagram import InstagramCopyAgent

        def _bad_callback(chunk):
            raise RuntimeError("callback broken")

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic_streaming(self._CHUNKS),
        ):
            # Não deve lançar exceção
            result = InstagramCopyAgent().generate_streaming(_CTX, on_chunk=_bad_callback)

        assert "source_url" in result

    def test_sem_callback_funciona_normalmente(self):
        from app.agents.copy.instagram import InstagramCopyAgent

        with patch(
            "app.agents.copy.base.Anthropic",
            return_value=_mock_anthropic_streaming(self._CHUNKS),
        ):
            result = InstagramCopyAgent().generate_streaming(_CTX)

        assert "source_url" in result


class TestGetAgent:
    @pytest.mark.parametrize(
        "channel,expected_class",
        [
            ("instagram", "InstagramCopyAgent"),
            ("linkedin", "LinkedinCopyAgent"),
            ("twitter", "TwitterCopyAgent"),
            ("youtube", "YoutubeCopyAgent"),
            ("email", "EmailCopyAgent"),
        ],
    )
    def test_retorna_agente_correto(self, channel, expected_class):
        from app.agents.copy import get_agent

        agent = get_agent(channel)
        assert type(agent).__name__ == expected_class

    def test_canal_desconhecido_lanca_value_error(self):
        from app.agents.copy import get_agent

        with pytest.raises(ValueError, match="Canal desconhecido"):
            get_agent("snapchat")

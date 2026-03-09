"""Testes unitários para os agentes de arte."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.agents.art import get_agent
from app.agents.art.base import ASPECT_RATIOS
from app.agents.art.static import StaticArtAgent
from app.agents.art.carousel import CarouselArtAgent
from app.agents.art.thumbnail import ThumbnailArtAgent

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_anthropic():
    """Mock da API Anthropic para build_prompt."""
    with patch("app.agents.art.base.Anthropic") as mock_cls:
        client = MagicMock()
        msg = MagicMock()
        msg.content = [MagicMock(text="professional marketing photo, clean design")]
        client.messages.create.return_value = msg
        mock_cls.return_value = client
        yield client


@pytest.fixture
def mock_stability_success():
    """Mock de resposta de sucesso da Stability AI."""
    import base64

    fake_png = base64.b64encode(b"PNG_BYTES_PLACEHOLDER").decode()
    with patch("app.agents.art.base.requests.post") as mock_post:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"finish_reason": "SUCCESS", "image": fake_png}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp
        yield mock_post


@pytest.fixture
def mock_stability_fail():
    """Mock de falha da Stability AI (sem key)."""
    with patch("app.agents.art.base.settings") as mock_cfg:
        mock_cfg.STABILITY_AI_KEY = ""
        mock_cfg.ANTHROPIC_API_KEY = ""
        yield mock_cfg


@pytest.fixture
def mock_drive():
    """Mock do upload para Google Drive."""
    with patch("app.agents.art.base.ArtAgent._upload_to_drive") as mock_upload:
        mock_upload.return_value = "https://drive.google.com/uc?id=fake123"
        yield mock_upload


# ── Testes de fábrica ─────────────────────────────────────────────────────────


class TestGetAgent:
    def test_retorna_static_agent(self):
        agent = get_agent("static")
        assert isinstance(agent, StaticArtAgent)

    def test_retorna_carousel_agent(self):
        agent = get_agent("carousel")
        assert isinstance(agent, CarouselArtAgent)

    def test_retorna_thumbnail_agent(self):
        agent = get_agent("thumbnail")
        assert isinstance(agent, ThumbnailArtAgent)

    def test_tipo_desconhecido_retorna_static(self):
        agent = get_agent("unknown_type")
        assert isinstance(agent, StaticArtAgent)


# ── Testes de configuração dos agentes ──────────────────────────────────────


class TestAgentConfig:
    def test_static_aspect_ratio(self):
        assert ASPECT_RATIOS["static"] == "1:1"

    def test_carousel_aspect_ratio(self):
        assert ASPECT_RATIOS["carousel"] == "4:5"

    def test_thumbnail_aspect_ratio(self):
        assert ASPECT_RATIOS["thumbnail"] == "16:9"

    def test_static_gera_1_slide(self):
        assert StaticArtAgent._slides_count == 1

    def test_carousel_gera_3_slides(self):
        assert CarouselArtAgent._slides_count == 3

    def test_thumbnail_gera_2_slides(self):
        assert ThumbnailArtAgent._slides_count == 2


# ── Testes de build_prompt ───────────────────────────────────────────────────


class TestBuildPrompt:
    def test_retorna_prompt_com_haiku(self, mock_anthropic):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.ANTHROPIC_API_KEY = "test-key"
            agent = StaticArtAgent()
            prompt = agent.build_prompt("Automação de marketing com IA", "instagram")
        assert "professional" in prompt.lower() or "marketing" in prompt.lower()

    def test_fallback_sem_key(self):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.ANTHROPIC_API_KEY = ""
            agent = StaticArtAgent()
            prompt = agent.build_prompt("qualquer texto", "linkedin")
        assert "linkedin" in prompt.lower()
        assert len(prompt) > 10

    def test_fallback_em_texto_vazio(self):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.ANTHROPIC_API_KEY = "test-key"
            agent = StaticArtAgent()
            prompt = agent.build_prompt("", "instagram")
        assert len(prompt) > 10

    def test_carousel_adiciona_contexto_slide(self, mock_anthropic):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.ANTHROPIC_API_KEY = "test-key"
            agent = CarouselArtAgent()
            prompt = agent.build_prompt("conteúdo do carrossel", "instagram")
        assert "carousel" in prompt.lower()

    def test_thumbnail_adiciona_contexto_youtube(self, mock_anthropic):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.ANTHROPIC_API_KEY = "test-key"
            agent = ThumbnailArtAgent()
            prompt = agent.build_prompt("vídeo sobre IA", "youtube")
        assert "thumbnail" in prompt.lower() or "youtube" in prompt.lower()


# ── Testes de geração com Stability AI ──────────────────────────────────────


class TestGenerate:
    def test_retorna_url_drive_com_stability(self, mock_stability_success, mock_drive):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.STABILITY_AI_KEY = "sk-test"
            cfg.ANTHROPIC_API_KEY = ""
            agent = StaticArtAgent()
            urls = agent.generate(
                pipeline_id="pipe-123",
                copy_id="copy-456",
                copy_text="Marketing digital com IA",
                channel="instagram",
            )
        assert len(urls) == 1
        assert "drive.google.com" in urls[0]

    def test_retorna_placeholder_sem_stability_key(self, mock_stability_fail):
        agent = StaticArtAgent()
        urls = agent.generate(
            pipeline_id="pipe-123",
            copy_id="copy-456",
            copy_text="Marketing digital",
            channel="instagram",
        )
        assert len(urls) == 1
        assert "placehold" in urls[0]

    def test_carousel_retorna_3_urls(self, mock_stability_fail):
        agent = CarouselArtAgent()
        urls = agent.generate("pipe-1", "copy-1", "texto", "instagram")
        assert len(urls) == 3

    def test_thumbnail_retorna_2_urls(self, mock_stability_fail):
        agent = ThumbnailArtAgent()
        urls = agent.generate("pipe-1", "copy-1", "texto", "youtube")
        assert len(urls) == 2

    def test_stability_finish_reason_erro_usa_placeholder(self):
        with patch("app.agents.art.base.requests.post") as mock_post:
            with patch("app.agents.art.base.settings") as cfg:
                cfg.STABILITY_AI_KEY = "sk-test"
                cfg.ANTHROPIC_API_KEY = ""
                resp = MagicMock()
                resp.json.return_value = {"finish_reason": "ERROR", "image": ""}
                resp.raise_for_status = MagicMock()
                mock_post.return_value = resp
                agent = StaticArtAgent()
                urls = agent.generate("pipe-1", "copy-1", "texto", "instagram")
        assert len(urls) == 1
        assert "placehold" in urls[0]

    def test_drive_upload_falha_usa_placeholder(self, mock_stability_success):
        with patch("app.agents.art.base.settings") as cfg:
            cfg.STABILITY_AI_KEY = "sk-test"
            cfg.ANTHROPIC_API_KEY = ""
            with patch("app.agents.art.base.ArtAgent._upload_to_drive", return_value=None):
                agent = StaticArtAgent()
                urls = agent.generate("pipe-1", "copy-1", "texto", "instagram")
        # _upload_to_drive retornou None, mas ainda gera placeholder como fallback
        assert len(urls) == 1

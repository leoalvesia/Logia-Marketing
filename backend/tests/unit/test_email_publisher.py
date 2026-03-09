"""Testes unitários para app/publishers/email.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


from app.publishers.email import _build_html, send_email

# ── Fixtures de copy_json ─────────────────────────────────────────────────────


def _make_copy(
    subject="Assunto Teste",
    preview_text="Preview curto",
    body_sections=None,
    cta="Leia mais",
    source_url="https://example.com/artigo",
) -> dict:
    return {
        "subject": subject,
        "preview_text": preview_text,
        "body_sections": body_sections
        or [{"heading": "Introdução", "content": "Conteúdo do parágrafo."}],
        "cta": cta,
        "source_url": source_url,
    }


# ── TestBuildHtml ─────────────────────────────────────────────────────────────


class TestBuildHtml:
    def test_html_valido_retornado(self):
        html = _build_html(_make_copy())
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_inclui_preview_text(self):
        html = _build_html(_make_copy(preview_text="Meu preview"))
        assert "Meu preview" in html

    def test_inclui_heading_da_secao(self):
        copy = _make_copy(body_sections=[{"heading": "Seção Especial", "content": "Texto."}])
        html = _build_html(copy)
        assert "Seção Especial" in html

    def test_inclui_content_da_secao(self):
        copy = _make_copy(body_sections=[{"heading": "H", "content": "Conteúdo relevante"}])
        html = _build_html(copy)
        assert "Conteúdo relevante" in html

    def test_inclui_url_e_cta(self):
        copy = _make_copy(cta="Ver artigo", source_url="https://example.com/post")
        html = _build_html(copy)
        assert "https://example.com/post" in html
        assert "Ver artigo" in html

    def test_multiplas_secoes(self):
        copy = _make_copy(
            body_sections=[
                {"heading": "Parte 1", "content": "Texto 1"},
                {"heading": "Parte 2", "content": "Texto 2"},
            ]
        )
        html = _build_html(copy)
        assert "Parte 1" in html
        assert "Parte 2" in html
        assert "Texto 2" in html

    def test_escapa_html_no_heading(self):
        copy = _make_copy(body_sections=[{"heading": "<script>alert(1)</script>", "content": "ok"}])
        html = _build_html(copy)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_escapa_html_no_content(self):
        copy = _make_copy(body_sections=[{"heading": "H", "content": "<b>bold</b>"}])
        html = _build_html(copy)
        assert "<b>" not in html
        assert "&lt;b&gt;" in html

    def test_secoes_vazias_nao_geram_erro(self):
        copy = _make_copy(body_sections=[])
        html = _build_html(copy)
        assert html  # não deve lançar exceção


# ── TestSendEmail ─────────────────────────────────────────────────────────────


def _resend_cfg(mock_cfg):
    mock_cfg.RESEND_API_KEY = "re_test_key"
    mock_cfg.EMAIL_FROM = "from@test.com"
    mock_cfg.SMTP_HOST = ""
    mock_cfg.SMTP_PORT = 587
    mock_cfg.SMTP_USER = ""
    mock_cfg.SMTP_PASS = ""


def _smtp_cfg(mock_cfg):
    mock_cfg.RESEND_API_KEY = ""
    mock_cfg.EMAIL_FROM = "from@test.com"
    mock_cfg.SMTP_HOST = "smtp.test.com"
    mock_cfg.SMTP_PORT = 587
    mock_cfg.SMTP_USER = "user"
    mock_cfg.SMTP_PASS = "pass"


class TestSendEmail:
    def test_resend_sucesso_retorna_true(self):
        with (
            patch("app.publishers.email.resend") as mock_resend,
            patch("app.publishers.email.settings") as mock_cfg,
        ):
            _resend_cfg(mock_cfg)
            mock_resend.Emails.send.return_value = {"id": "msg_abc"}

            result = send_email(_make_copy(), "dest@test.com")

        assert result is True
        mock_resend.Emails.send.assert_called_once()

    def test_resend_usa_api_key_da_config(self):
        with (
            patch("app.publishers.email.resend") as mock_resend,
            patch("app.publishers.email.settings") as mock_cfg,
        ):
            _resend_cfg(mock_cfg)
            mock_resend.Emails.send.return_value = {"id": "x"}

            send_email(_make_copy(), "dest@test.com")

        assert mock_resend.api_key == "re_test_key"

    def test_resend_falha_usa_smtp_fallback(self):
        with (
            patch("app.publishers.email.resend") as mock_resend,
            patch("app.publishers.email.smtplib") as mock_smtp,
            patch("app.publishers.email.settings") as mock_cfg,
        ):
            mock_cfg.RESEND_API_KEY = "re_key"
            mock_cfg.EMAIL_FROM = "from@test.com"
            mock_cfg.SMTP_HOST = "smtp.host"
            mock_cfg.SMTP_PORT = 587
            mock_cfg.SMTP_USER = "u"
            mock_cfg.SMTP_PASS = "p"

            mock_resend.Emails.send.side_effect = Exception("Resend down")
            smtp_instance = MagicMock()
            mock_smtp.SMTP.return_value.__enter__ = MagicMock(return_value=smtp_instance)
            mock_smtp.SMTP.return_value.__exit__ = MagicMock(return_value=False)

            result = send_email(_make_copy(), "dest@test.com")

        assert result is True
        smtp_instance.sendmail.assert_called_once()

    def test_sem_api_key_usa_smtp_diretamente(self):
        with (
            patch("app.publishers.email.smtplib") as mock_smtp,
            patch("app.publishers.email.settings") as mock_cfg,
        ):
            _smtp_cfg(mock_cfg)
            smtp_instance = MagicMock()
            mock_smtp.SMTP.return_value.__enter__ = MagicMock(return_value=smtp_instance)
            mock_smtp.SMTP.return_value.__exit__ = MagicMock(return_value=False)

            result = send_email(_make_copy(), "dest@test.com")

        assert result is True

    def test_ambos_falham_retorna_false(self):
        with (
            patch("app.publishers.email.resend") as mock_resend,
            patch("app.publishers.email.smtplib") as mock_smtp,
            patch("app.publishers.email.settings") as mock_cfg,
        ):
            mock_cfg.RESEND_API_KEY = "re_key"
            mock_cfg.EMAIL_FROM = "from@test.com"
            mock_cfg.SMTP_HOST = "smtp.host"
            mock_cfg.SMTP_PORT = 587
            mock_cfg.SMTP_USER = "u"
            mock_cfg.SMTP_PASS = "p"

            mock_resend.Emails.send.side_effect = Exception("Resend down")
            mock_smtp.SMTP.side_effect = Exception("SMTP down")

            result = send_email(_make_copy(), "dest@test.com")

        assert result is False

    def test_sem_smtp_host_sem_api_key_retorna_false(self):
        """Se não há RESEND_API_KEY e SMTP_HOST está vazio, retorna False."""
        with patch("app.publishers.email.settings") as mock_cfg:
            mock_cfg.RESEND_API_KEY = ""
            mock_cfg.EMAIL_FROM = "from@test.com"
            mock_cfg.SMTP_HOST = ""
            mock_cfg.SMTP_PORT = 587
            mock_cfg.SMTP_USER = ""
            mock_cfg.SMTP_PASS = ""

            result = send_email(_make_copy(), "dest@test.com")

        assert result is False

    def test_smtp_starttls_chamado_quando_usuario_configurado(self):
        with (
            patch("app.publishers.email.smtplib") as mock_smtp,
            patch("app.publishers.email.settings") as mock_cfg,
        ):
            _smtp_cfg(mock_cfg)
            smtp_instance = MagicMock()
            mock_smtp.SMTP.return_value.__enter__ = MagicMock(return_value=smtp_instance)
            mock_smtp.SMTP.return_value.__exit__ = MagicMock(return_value=False)

            send_email(_make_copy(), "dest@test.com")

        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("user", "pass")

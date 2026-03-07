"""Testes unitários para app/storage/google_drive.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.storage.google_drive import _guess_mime, upload_image


# ── Helpers de setup dos mocks ────────────────────────────────────────────────


def _make_drive_service(file_id: str = "abc123") -> MagicMock:
    """Monta um mock do service object do Google Drive."""
    svc = MagicMock()
    svc.files.return_value.create.return_value.execute.return_value = {"id": file_id}
    svc.permissions.return_value.create.return_value.execute.return_value = {}
    return svc


def _drive_patches(svc: MagicMock, folder_id: str = "folder_xyz"):
    """Context manager que aplica todos os patches necessários para upload_image."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with (
            patch("app.storage.google_drive.build", return_value=svc),
            patch("app.storage.google_drive.service_account") as mock_sa,
            patch("app.storage.google_drive.MediaFileUpload"),
            patch("app.storage.google_drive.settings") as mock_cfg,
        ):
            mock_cfg.GOOGLE_DRIVE_FOLDER_ID = folder_id
            mock_cfg.GOOGLE_SERVICE_ACCOUNT_JSON = "/path/to/sa.json"
            mock_sa.Credentials.from_service_account_file.return_value = MagicMock()
            yield mock_cfg, mock_sa

    return _ctx()


# ── TestUploadImage ───────────────────────────────────────────────────────────


class TestUploadImage:
    def test_retorna_url_drive_correta(self):
        svc = _make_drive_service(file_id="fileId123")
        with _drive_patches(svc):
            url = upload_image("/tmp/test.png")
        assert url == "https://drive.google.com/uc?id=fileId123"

    def test_torna_arquivo_publico(self):
        svc = _make_drive_service(file_id="fileId123")
        with _drive_patches(svc):
            upload_image("/tmp/test.png")
        svc.permissions.return_value.create.assert_called_once_with(
            fileId="fileId123",
            body={"role": "reader", "type": "anyone"},
        )

    def test_usa_folder_id_da_config(self):
        svc = _make_drive_service()
        with _drive_patches(svc, folder_id="myFolder"):
            upload_image("/tmp/test.png")
        call_kwargs = svc.files.return_value.create.call_args[1]
        assert "myFolder" in call_kwargs["body"]["parents"]

    def test_nome_do_arquivo_no_metadata(self):
        svc = _make_drive_service()
        with _drive_patches(svc):
            upload_image("/tmp/imagens/foto.jpg")
        call_kwargs = svc.files.return_value.create.call_args[1]
        assert call_kwargs["body"]["name"] == "foto.jpg"

    def test_sem_folder_id_lanca_runtime_error(self):
        with patch("app.storage.google_drive.settings") as mock_cfg:
            mock_cfg.GOOGLE_DRIVE_FOLDER_ID = ""
            with pytest.raises(RuntimeError, match="GOOGLE_DRIVE_FOLDER_ID"):
                upload_image("/tmp/test.png")

    def test_quota_excedida_lanca_http_error(self):
        from googleapiclient.errors import HttpError

        mock_resp = MagicMock()
        mock_resp.status = 403
        svc = MagicMock()
        svc.files.return_value.create.return_value.execute.side_effect = HttpError(
            mock_resp, b"userRateLimitExceeded"
        )

        with _drive_patches(svc):
            with pytest.raises(HttpError):
                upload_image("/tmp/test.png")

    def test_erro_de_rede_lanca_excecao(self):
        svc = MagicMock()
        svc.files.return_value.create.return_value.execute.side_effect = ConnectionError(
            "network failure"
        )
        with _drive_patches(svc):
            with pytest.raises(ConnectionError):
                upload_image("/tmp/test.png")

    def test_drive_indisponivel_lanca_runtime_error(self):
        """Se google-api-python-client não estiver disponível, levanta RuntimeError."""
        with (
            patch("app.storage.google_drive._DRIVE_AVAILABLE", False),
            patch("app.storage.google_drive.settings") as mock_cfg,
        ):
            mock_cfg.GOOGLE_DRIVE_FOLDER_ID = "folder"
            with pytest.raises(RuntimeError, match="google-api-python-client"):
                upload_image("/tmp/test.png")


# ── TestGuessMime ─────────────────────────────────────────────────────────────


class TestGuessMime:
    def test_png(self):
        assert _guess_mime("imagem.png") == "image/png"

    def test_jpg(self):
        assert _guess_mime("foto.jpg") == "image/jpeg"

    def test_jpeg(self):
        assert _guess_mime("foto.jpeg") == "image/jpeg"

    def test_webp(self):
        assert _guess_mime("banner.webp") == "image/webp"

    def test_gif(self):
        assert _guess_mime("anim.gif") == "image/gif"

    def test_extensao_desconhecida_retorna_jpeg(self):
        assert _guess_mime("file.bmp") == "image/jpeg"

    def test_sem_extensao_retorna_jpeg(self):
        assert _guess_mime("sem_extensao") == "image/jpeg"

    def test_maiuscula_normalizada(self):
        assert _guess_mime("foto.PNG") == "image/png"

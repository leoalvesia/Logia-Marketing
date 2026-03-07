"""Upload de imagens para Google Drive via service account."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

from app.config import settings  # noqa: E402 — import here to allow patch in tests

# Importação no nível do módulo para permitir patch em testes
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google.oauth2 import service_account

    _DRIVE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DRIVE_AVAILABLE = False


_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def upload_image(image_path: str) -> str:
    """Faz upload de uma imagem para o Google Drive e retorna URL pública.

    Args:
        image_path: Caminho local do arquivo de imagem.

    Returns:
        URL pública no formato ``https://drive.google.com/uc?id={file_id}``.

    Raises:
        RuntimeError: Se dependências ou configurações estiverem faltando.
        HttpError: Em erros da API do Drive (quota, permissão etc.).
    """
    if not _DRIVE_AVAILABLE:
        raise RuntimeError(
            "google-api-python-client não instalado. Execute: "
            "pip install google-api-python-client google-auth"
        )

    if not settings.GOOGLE_DRIVE_FOLDER_ID:
        raise RuntimeError(
            "GOOGLE_DRIVE_FOLDER_ID não configurado. Defina no .env."
        )

    try:
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=_DRIVE_SCOPES,
        )
        svc = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": os.path.basename(image_path),
            "parents": [settings.GOOGLE_DRIVE_FOLDER_ID],
        }
        media = MediaFileUpload(
            image_path, mimetype=_guess_mime(image_path), resumable=True
        )
        file = (
            svc.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        file_id: str = file["id"]

        svc.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        url = f"https://drive.google.com/uc?id={file_id}"
        logger.info("Drive upload OK: %s → %s", image_path, url)
        return url

    except HttpError as exc:
        if exc.resp.status == 403:
            logger.error("Drive: quota excedida ou permissão negada: %s", exc)
        else:
            logger.error("Drive: HttpError %s: %s", exc.resp.status, exc)
        raise
    except Exception as exc:
        logger.error("Drive: erro inesperado ao fazer upload de %s: %s", image_path, exc)
        raise


def _guess_mime(path: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(os.path.splitext(path)[1].lower(), "image/jpeg")

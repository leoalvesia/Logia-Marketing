"""Base para agentes de arte — geração via Stability AI + upload Google Drive."""

from __future__ import annotations

import base64
import logging
import os
import tempfile

import requests
from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Aspect ratios suportados pela Stability AI v2beta
ASPECT_RATIOS = {
    "static": "1:1",
    "carousel": "4:5",
    "thumbnail": "16:9",
}

_STABILITY_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

_STYLE_NEGATIVE = (
    "blurry, low quality, distorted text, watermark, signature, "
    "amateur, overexposed, underexposed, low resolution, pixelated"
)


class ArtAgent:
    """Agente base para geração de imagens via Stability AI.

    Subclasses definem `art_type` e podem sobrescrever `_slides_count`.
    """

    art_type: str = "static"
    _slides_count: int = 1  # carrossel sobrescreve para 3–5

    # ── Geração de prompt ────────────────────────────────────────────────────

    def build_prompt(self, copy_text: str, channel: str) -> str:
        """Usa Claude Haiku para transformar o texto da copy em prompt de imagem SD.

        Retorna prompt em inglês otimizado para Stable Diffusion.
        Fallback para prompt genérico se a API falhar.
        """
        if not settings.ANTHROPIC_API_KEY or not copy_text.strip():
            return self._fallback_prompt(channel)

        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=_HAIKU_MODEL,
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Create a concise Stable Diffusion image prompt (max 150 words) "
                            f"for a {channel} marketing post based on this copy:\n\n"
                            f"{copy_text[:400]}\n\n"
                            "Requirements:\n"
                            "- Professional marketing visual\n"
                            "- Modern, clean design\n"
                            "- No text or typography in image\n"
                            "- High quality, photorealistic or clean illustration\n"
                            "- Relevant to the topic\n"
                            "Output ONLY the prompt, no explanations."
                        ),
                    }
                ],
            )
            prompt = response.content[0].text.strip()
            return f"{prompt}, professional marketing photo, high quality, 8k"
        except Exception as exc:
            logger.warning("ArtAgent.build_prompt falhou: %s", exc)
            return self._fallback_prompt(channel)

    def _fallback_prompt(self, channel: str) -> str:
        return (
            f"Professional {channel} marketing image, modern minimalist design, "
            "clean background, business concept, high quality photography, 8k"
        )

    # ── Chamada à Stability AI ───────────────────────────────────────────────

    def _call_stability(self, prompt: str, aspect_ratio: str) -> bytes | None:
        """Chama a API Stability AI v2beta e retorna bytes da imagem PNG.

        Retorna None se a chave não estiver configurada ou em erro.
        """
        if not settings.STABILITY_AI_KEY:
            logger.warning("STABILITY_AI_KEY não configurado — retornando placeholder")
            return None

        try:
            # Stability AI v2beta exige multipart/form-data.
            # Passa todos os campos via `files` para forçar o content-type correto
            # sem enviar um arquivo binário desnecessário.
            resp = requests.post(
                _STABILITY_URL,
                headers={
                    "Authorization": f"Bearer {settings.STABILITY_AI_KEY}",
                    "Accept": "application/json",
                },
                files={
                    "prompt": (None, prompt),
                    "aspect_ratio": (None, aspect_ratio),
                    "output_format": (None, "png"),
                    "negative_prompt": (None, _STYLE_NEGATIVE),
                },
                timeout=60,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("finish_reason") == "SUCCESS":
                return base64.b64decode(payload["image"])
            logger.warning("Stability AI finish_reason=%s", payload.get("finish_reason"))
            return None
        except Exception as exc:
            logger.error("_call_stability: %s", exc)
            return None

    # ── Upload para Google Drive ─────────────────────────────────────────────

    def _upload_to_drive(self, image_bytes: bytes, filename: str) -> str | None:
        """Salva bytes em arquivo temp e faz upload para o Google Drive.

        Retorna URL pública ou None em falha.
        """
        from app.storage.google_drive import upload_image

        try:
            suffix = ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name

            url = upload_image(tmp_path)
            return url
        except Exception as exc:
            logger.error("_upload_to_drive: %s", exc)
            return None
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ── Ponto de entrada público ─────────────────────────────────────────────

    def generate(self, pipeline_id: str, copy_id: str, copy_text: str, channel: str) -> list[str]:
        """Gera imagem(ns) e retorna lista de URLs públicas.

        Args:
            pipeline_id: ID do pipeline para nomear os arquivos.
            copy_id: ID da copy associada.
            copy_text: Texto da copy para gerar o prompt.
            channel: Canal da copy (instagram, linkedin, etc.).

        Returns:
            Lista de URLs públicas. Vazia se falhar completamente.
        """
        aspect_ratio = ASPECT_RATIOS.get(self.art_type, "1:1")
        urls: list[str] = []

        for slide_idx in range(self._slides_count):
            prompt = self.build_prompt(copy_text, channel)
            image_bytes = self._call_stability(prompt, aspect_ratio)

            url = None
            if image_bytes:
                filename = f"{pipeline_id[:8]}_{self.art_type}_{slide_idx}.png"
                url = self._upload_to_drive(image_bytes, filename)

            if not url:
                # Sem key, erro na API ou falha no upload — placeholder para dev
                url = (
                    f"https://placehold.co/{self._placeholder_size()}/"
                    f"1A1A1A/6366F1?text=Arte+{self.art_type}"
                )

            urls.append(url)

        return urls

    def _placeholder_size(self) -> str:
        sizes = {"static": "1080x1080", "carousel": "864x1080", "thumbnail": "1280x720"}
        return sizes.get(self.art_type, "1080x1080")

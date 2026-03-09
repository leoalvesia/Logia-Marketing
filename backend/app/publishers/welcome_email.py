"""Email de boas-vindas enviado após registro de novo usuário.

Usa Resend SDK (mesmo padrão do email.py).
Importado no nível do módulo para testabilidade via patch().
"""

from __future__ import annotations

import resend  # type: ignore[import-untyped]

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_welcome_html(name: str) -> str:
    safe_name = _escape(name)
    pipeline_url = "https://app.logia.com.br/pipeline"

    return (
        '<!DOCTYPE html><html lang="pt-BR">'
        "<head>"
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        "<title>Bem-vindo à Logia</title>"
        "</head>"
        '<body style="margin:0;padding:0;background:#0F0F0F;font-family:Arial,sans-serif;">'
        '<table width="100%" cellpadding="0" cellspacing="0" style="background:#0F0F0F;padding:32px 0;">'
        '<tr><td align="center">'
        '<table width="560" cellpadding="0" cellspacing="0"'
        ' style="background:#1A1A1A;border-radius:12px;border:1px solid #2E2E2E;">'
        '<tr><td style="padding:40px 48px;">'
        # Header com logo
        '<div style="text-align:center;margin-bottom:32px;">'
        '<div style="display:inline-flex;align-items:center;justify-content:center;'
        'width:52px;height:52px;background:#6366F1;border-radius:12px;margin-bottom:12px;">'
        '<span style="color:#fff;font-size:26px;">&#9889;</span>'
        "</div>"
        '<p style="margin:0;color:#F9FAFB;font-size:22px;font-weight:bold;">Logia</p>'
        "</div>"
        # Corpo
        f'<h2 style="color:#F9FAFB;font-size:20px;font-weight:600;margin:0 0 16px;">'
        f"Bem-vindo, {safe_name}!</h2>"
        '<p style="color:#9CA3AF;font-size:15px;line-height:1.65;margin:0 0 8px;">'
        "Sua conta está pronta. Em menos de 3 minutos você vai criar seu primeiro "
        "post completo — pesquisa de tendências, copy otimizada e arte visual, "
        "tudo gerado automaticamente."
        "</p>"
        '<p style="color:#9CA3AF;font-size:15px;line-height:1.65;margin:0 0 32px;">'
        "Clique no botão abaixo para começar:"
        "</p>"
        # CTA
        '<div style="text-align:center;margin-bottom:32px;">'
        f'<a href="{pipeline_url}"'
        ' style="display:inline-block;background:#4F46E5;color:#ffffff;'
        "text-decoration:none;padding:14px 36px;border-radius:8px;"
        'font-weight:bold;font-size:15px;">Criar meu primeiro post</a>'
        "</div>"
        # Rodapé
        '<div style="border-top:1px solid #2E2E2E;padding-top:24px;margin-top:8px;">'
        '<p style="color:#6B7280;font-size:13px;line-height:1.6;margin:0 0 4px;">'
        "Dúvidas? Responda a este email — lemos todos."
        "</p>"
        '<p style="color:#6B7280;font-size:13px;margin:0;">'
        "— Leonardo / Equipe Logia"
        "</p>"
        "</div>"
        "</td></tr>"
        "</table>"
        "</td></tr>"
        "</table>"
        "</body></html>"
    )


def send_welcome_email(name: str, email: str) -> bool:
    """Envia email de boas-vindas ao usuário recém-registrado.

    Fire-and-forget: falha silenciosa com log de erro (nunca bloqueia o registro).

    Args:
        name:  Nome do usuário (escapado antes de inserir no HTML).
        email: Endereço de destino.

    Returns:
        True se enviado com sucesso, False em caso de falha ou sem API key.
    """
    if not settings.RESEND_API_KEY:
        logger.info(
            "welcome_email_skipped",
            reason="RESEND_API_KEY não configurado",
            email=email,
        )
        return False

    try:
        resend.api_key = settings.RESEND_API_KEY
        params: dict = {
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Bem-vindo à Logia — seu primeiro post em minutos",
            "html": _build_welcome_html(name),
        }
        response = resend.Emails.send(params)
        msg_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", "")
        logger.info("welcome_email_sent", email=email, msg_id=msg_id)
        return True
    except Exception as exc:
        logger.error("welcome_email_failed", email=email, error=str(exc))
        return False

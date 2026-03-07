"""Envio de email marketing via Resend SDK com fallback SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import resend  # type: ignore[import-untyped]

from app.config import settings  # noqa: E402 — import here to allow patch in tests

logger = logging.getLogger(__name__)


# ── HTML builder ──────────────────────────────────────────────────────────────


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _sections_to_html(sections: list[dict]) -> str:
    parts: list[str] = []
    for s in sections:
        heading = _escape(s.get("heading", ""))
        content = _escape(s.get("content", ""))
        if heading:
            parts.append(
                f'<h2 style="color:#111;font-size:18px;margin:24px 0 8px;">'
                f"{heading}</h2>"
            )
        if content:
            parts.append(
                f'<p style="color:#444;font-size:15px;line-height:1.6;margin:0 0 16px;">'
                f"{content}</p>"
            )
    return "\n".join(parts)


def _build_html(copy_json: dict) -> str:
    """Converte copy_json do agente email em HTML responsivo."""
    preview = _escape(copy_json.get("preview_text", ""))
    sections_html = _sections_to_html(copy_json.get("body_sections", []))
    cta = _escape(copy_json.get("cta", ""))
    source_url = copy_json.get("source_url", "#")

    return (
        '<!DOCTYPE html><html lang="pt-BR">'
        "<head>"
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f"<title>{_escape(copy_json.get('subject', ''))}</title>"
        "</head>"
        '<body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,sans-serif;">'
        '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 0;">'
        "<tr><td align=\"center\">"
        '<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;">'
        '<tr><td style="padding:32px 40px;">'
        f'<span style="display:none;font-size:1px;color:#fefefe;max-height:0;max-width:0;opacity:0;overflow:hidden;">{preview}</span>'
        f"{sections_html}"
        '<div style="text-align:center;margin-top:32px;">'
        f'<a href="{source_url}" style="background:#1a56db;color:#fff;text-decoration:none;'
        f'padding:14px 28px;border-radius:6px;font-weight:bold;display:inline-block;">{cta}</a>'
        "</div>"
        "</td></tr>"
        "</table>"
        "</td></tr>"
        "</table>"
        "</body></html>"
    )


# ── Senders ───────────────────────────────────────────────────────────────────


def _send_via_resend(html: str, subject: str, recipient: str) -> str:
    """Envia via Resend SDK. Retorna message_id em caso de sucesso."""
    resend.api_key = settings.RESEND_API_KEY
    params: dict = {
        "from": settings.EMAIL_FROM,
        "to": [recipient],
        "subject": subject,
        "html": html,
    }
    response = resend.Emails.send(params)
    msg_id: str = (
        response.get("id") if isinstance(response, dict) else getattr(response, "id", "")
    )
    return msg_id


def _send_via_smtp(html: str, subject: str, recipient: str) -> bool:
    """Fallback SMTP via smtplib. Retorna True em caso de sucesso."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST não configurado — fallback SMTP ignorado")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_USER:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        smtp.sendmail(settings.EMAIL_FROM, recipient, msg.as_string())
    return True


# ── Ponto de entrada público ──────────────────────────────────────────────────


def send_email(copy_json: dict, recipient: str) -> bool:
    """Envia email marketing a partir de copy_json do agente email.

    Tenta Resend primeiro; se falhar (ou sem API key), tenta SMTP.

    Args:
        copy_json: Dict com subject, preview_text, body_sections, cta, source_url.
        recipient:  Endereço de email do destinatário.

    Returns:
        True se enviado com sucesso, False se ambos os métodos falharem.
    """
    subject = copy_json.get("subject", "")
    html = _build_html(copy_json)

    # ── Primário: Resend ─────────────────────────────────────────────────────
    if settings.RESEND_API_KEY:
        try:
            msg_id = _send_via_resend(html, subject, recipient)
            logger.info("Email enviado via Resend: message_id=%s → %s", msg_id, recipient)
            return True
        except Exception as exc:
            logger.error("Resend falhou (%s) — tentando SMTP", exc)

    # ── Fallback: SMTP ───────────────────────────────────────────────────────
    try:
        ok = _send_via_smtp(html, subject, recipient)
        if ok:
            logger.info("Email enviado via SMTP → %s", recipient)
        return ok
    except Exception as exc:
        logger.error("SMTP também falhou: %s", exc)
        return False

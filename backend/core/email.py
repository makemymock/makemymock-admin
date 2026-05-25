"""Email transport for the admin service.

Mirrors the Client backend's transport selection: Brevo HTTPS when an
API key is configured (works from any cloud host), otherwise direct
SMTP via aiosmtplib for local dev.

Templates live next to the module that uses them — `promotional_email`
owns `promo.html`. The renderer is generic so other modules can drop
their own templates without touching this file.
"""

from __future__ import annotations

import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Iterable

import aiosmtplib
import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config.settings import settings

logger = logging.getLogger(__name__)

# Templates are discovered relative to each module — we expose a generic
# loader factory so the call site can specify which folder to read from.
_MODULES_ROOT = Path(__file__).resolve().parent.parent / "modules"


def _env_for(module_name: str) -> Environment:
    template_dir = _MODULES_ROOT / module_name / "email_templates"
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        enable_async=False,
    )


def render_template(module_name: str, template_name: str, context: dict[str, Any]) -> str:
    env = _env_for(module_name)
    template = env.get_template(template_name)
    return template.render(**context)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> None:
    if settings.BREVO_API_KEY:
        await _send_via_brevo(to_email, subject, html_body, text_body)
    else:
        await _send_via_smtp(to_email, subject, html_body, text_body)


# ---------------------------------------------------------------------------
# Brevo HTTPS transport
# ---------------------------------------------------------------------------

_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


async def _send_via_brevo(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None,
) -> None:
    payload: dict[str, Any] = {
        "sender": {
            "email": settings.SMTP_EMAIL,
            "name": settings.SMTP_FROM_NAME,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if text_body:
        payload["textContent"] = text_body

    headers = {
        "api-key": settings.BREVO_API_KEY,
        "accept": "application/json",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(_BREVO_URL, headers=headers, json=payload)
        if response.status_code >= 400:
            logger.error(
                "Brevo rejected email to %s (status=%s body=%s)",
                to_email, response.status_code, response.text,
            )
            response.raise_for_status()
        logger.info("Email sent to %s via Brevo (subject=%s)", to_email, subject)
    except Exception as exc:
        logger.exception("Failed to send Brevo email to %s: %s", to_email, exc)
        raise


async def send_email_batch_via_brevo(
    recipients: Iterable[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> None:
    """Send the same message to many recipients in a single Brevo call.

    Brevo allows up to 1000 addresses per request via `messageVersions`
    or via individual `to[]` entries with bcc semantics. We keep it
    simple and let the caller decide on chunking — the service module
    splits its full recipient list into chunks before calling this.

    Each recipient appears only on their own copy (no bcc cross-leak)
    because we send one Brevo request per recipient inside the batch.
    Concurrency is bounded by the service module.
    """
    raise NotImplementedError(
        "Batch send is implemented at the service layer using `send_email` "
        "with bounded concurrency; this helper is reserved for true bulk."
    )


# ---------------------------------------------------------------------------
# SMTP transport
# ---------------------------------------------------------------------------

async def _send_via_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None,
) -> None:
    if not (settings.SMTP_HOST and settings.SMTP_EMAIL and settings.SMTP_PASSWORD):
        raise RuntimeError(
            "SMTP credentials are not configured. Set SMTP_HOST/SMTP_EMAIL/"
            "SMTP_PASSWORD or provide a BREVO_API_KEY."
        )
    message = EmailMessage()
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body or "This email requires an HTML-capable client.")
    message.add_alternative(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_USE_TLS,
            timeout=15,
        )
        logger.info("Email sent to %s via SMTP (subject=%s)", to_email, subject)
    except Exception as exc:
        logger.exception("Failed to send SMTP email to %s: %s", to_email, exc)
        raise

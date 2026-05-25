"""Promotional email dispatcher.

The admin types a subject + body in the UI, picks recipients, and clicks
send. We render each message (the same HTML template for everyone, so
nobody can see anyone else's address) and dispatch with bounded
concurrency so we don't blow past provider rate limits.
"""

from __future__ import annotations

import asyncio
import logging
import re
from html import escape

from config.settings import settings
from core.email import render_template, send_email
from core.exceptions import NoRecipients, TooManyRecipients
from modules.promotional_email.schema import (
    PerRecipientResult,
    PreviewRequest,
    PreviewResponse,
    SendPromoRequest,
    SendPromoResponse,
)

logger = logging.getLogger(__name__)


class PromoEmailService:
    @staticmethod
    def _render_html(
        body: str,
        *,
        use_template: bool,
        preserve_line_breaks: bool,
        subject: str,
    ) -> str:
        if not use_template:
            # Admin supplied raw HTML — render verbatim. They're trusted.
            return body

        # Wrap plain text in paragraphs. We escape HTML to prevent
        # accidental tag injection from a copy-pasted body.
        text = body.strip()
        if preserve_line_breaks:
            paragraphs = [escape(p).replace("\n", "<br/>") for p in re.split(r"\n{2,}", text)]
            content_html = "".join(f"<p>{p}</p>" for p in paragraphs if p)
        else:
            content_html = f"<p>{escape(text)}</p>"

        return render_template(
            "promotional_email",
            "promo.html",
            {
                "app_name": settings.APP_NAME.replace("-Admin", ""),
                "subject": subject,
                "content_html": content_html,
            },
        )

    async def preview(self, payload: PreviewRequest) -> PreviewResponse:
        html = self._render_html(
            payload.body,
            use_template=payload.use_template,
            preserve_line_breaks=payload.preserve_line_breaks,
            subject=payload.subject,
        )
        return PreviewResponse(subject=payload.subject, html=html)

    async def send(self, payload: SendPromoRequest) -> SendPromoResponse:
        unique_recipients = list(dict.fromkeys(r.lower().strip() for r in payload.recipients))
        if not unique_recipients:
            raise NoRecipients()
        if len(unique_recipients) > settings.PROMO_EMAIL_MAX_RECIPIENTS:
            raise TooManyRecipients(
                f"Batch limited to {settings.PROMO_EMAIL_MAX_RECIPIENTS} recipients; "
                f"got {len(unique_recipients)}."
            )

        html = self._render_html(
            payload.body,
            use_template=payload.use_template,
            preserve_line_breaks=payload.preserve_line_breaks,
            subject=payload.subject,
        )

        # Plain-text fallback for clients that block HTML.
        text = re.sub(r"<[^>]+>", "", payload.body).strip()

        semaphore = asyncio.Semaphore(max(1, settings.PROMO_EMAIL_CONCURRENCY))
        results: list[PerRecipientResult] = []

        async def _send_one(email: str) -> PerRecipientResult:
            async with semaphore:
                try:
                    await send_email(email, payload.subject, html, text)
                    return PerRecipientResult(email=email, status="sent")
                except Exception as exc:
                    logger.warning("Promo send failed for %s: %s", email, exc)
                    return PerRecipientResult(email=email, status="failed", error=str(exc))

        results = await asyncio.gather(*[_send_one(r) for r in unique_recipients])

        sent = sum(1 for r in results if r.status == "sent")
        failed = len(results) - sent
        return SendPromoResponse(
            requested=len(unique_recipients),
            sent=sent,
            failed=failed,
            results=results,
        )

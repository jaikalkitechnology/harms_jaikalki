"""SMTP email sender with simple Jinja-style templates.

Uses aiosmtplib for non-blocking sends. Templates live as plain Python
constants — keep them small and brand-consistent. If `EMAIL_ENABLED` is
False the service logs the would-be email and returns success so dev /
test environments don't depend on a live SMTP server.
"""
from __future__ import annotations

import logging
import re
from email.message import EmailMessage
from typing import Optional

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


_BRAND_HEADER = (
    "<div style='background:#3D2817;color:#F4B71F;padding:16px 24px;"
    "font-family:Helvetica,Arial,sans-serif;font-size:18px;font-weight:bold;'>"
    "Jaikalki Technology Pvt Ltd</div>"
)

_BRAND_FOOTER = (
    "<div style='font-family:Helvetica,Arial,sans-serif;font-size:11px;"
    "color:#8c715a;padding:16px 24px;background:#FBF6E9;'>"
    "This is an automated message from the Jaikalki HRMS. "
    "If you weren't expecting it, please contact hr@jaikalki.com.</div>"
)


def _wrap_html(content_html: str) -> str:
    return (
        "<!doctype html><html><body style='margin:0;background:#fafaf7;'>"
        f"{_BRAND_HEADER}"
        f"<div style='padding:24px;font-family:Helvetica,Arial,sans-serif;"
        f"color:#3D2817;font-size:14px;line-height:1.55;'>{content_html}</div>"
        f"{_BRAND_FOOTER}"
        "</body></html>"
    )


def _interpolate(template: str, params: dict) -> str:
    """Replace {{name}} with params['name']. Lightweight, no Jinja required."""

    def repl(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(params.get(key, m.group(0)))

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", repl, template)


# ── Templates ────────────────────────────────────────────────────────
TEMPLATES: dict[str, dict[str, str]] = {
    "password_reset_otp": {
        "subject": "Your Jaikalki HRMS password reset code",
        "html": (
            "<p>Hi {{name}},</p>"
            "<p>We received a request to reset your Jaikalki HRMS password.</p>"
            "<p>Your one-time code is:</p>"
            "<p style='font-size:32px;font-weight:bold;letter-spacing:6px;"
            "background:#FEF3C7;padding:12px 16px;display:inline-block;"
            "border-radius:6px;color:#3D2817;'>{{otp}}</p>"
            "<p>This code expires in {{ttl}} minutes. If you didn't request "
            "this, please ignore this email.</p>"
        ),
    },
    "approval_pending": {
        "subject": "[Jaikalki HRMS] {{request_type}} pending your approval",
        "html": (
            "<p>Hi {{name}},</p>"
            "<p>You have a pending <b>{{request_type}}</b> approval:</p>"
            "<blockquote style='border-left:3px solid #F4B71F;padding-left:12px;"
            "color:#5C3D24;'>{{title}}</blockquote>"
            "<p>{{summary}}</p>"
            "<p>Open the HRMS admin portal to review and decide.</p>"
        ),
    },
    "resignation_submitted": {
        "subject": "Resignation submitted — {{employee_name}}",
        "html": (
            "<p>{{employee_name}} ({{employee_code}}) has submitted a "
            "resignation, effective {{last_day}}.</p>"
            "<p>Reason: {{reason}}</p>"
            "<p>Please review in the HRMS admin portal.</p>"
        ),
    },
    "compliance_digest": {
        "subject": "[Jaikalki HRMS] Daily compliance digest",
        "html": (
            "<p>Daily compliance digest for {{date}}:</p>"
            "<ul>"
            "<li><b>{{pending_approvals}}</b> approvals waiting</li>"
            "<li><b>{{overdue_verifications}}</b> verifications past SLA</li>"
            "<li><b>{{pending_self_reviews}}</b> employees yet to submit "
            "self review</li>"
            "<li><b>{{posh_uncertified}}</b> employees without an active "
            "POSH certificate</li>"
            "</ul>"
            "<p>Open the Director Dashboard for the full picture.</p>"
        ),
    },
}


async def send_template_email(
    *,
    to_email: str,
    to_name: Optional[str],
    template: str,
    params: dict,
) -> tuple[bool, Optional[str]]:
    """Render a registered template + send. Returns (ok, error)."""
    spec = TEMPLATES.get(template)
    if not spec:
        return False, f"unknown template: {template}"
    subject = _interpolate(spec["subject"], params)
    html = _interpolate(spec["html"], params)
    return await send_email(
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        html=html,
    )


async def send_email(
    *,
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html: str,
    plain: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Send a single email via SMTP. Returns (ok, error)."""
    if not settings.EMAIL_ENABLED:
        logger.info(
            "EMAIL_ENABLED=False, would send to=%s subject=%s",
            to_email, subject,
        )
        return True, None

    msg = EmailMessage()
    msg["From"] = (
        f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    )
    msg["To"] = (
        f"{to_name} <{to_email}>" if to_name else to_email
    )
    msg["Subject"] = subject
    if plain:
        msg.set_content(plain)
    else:
        # crude html->text fallback
        msg.set_content(re.sub(r"<[^>]+>", "", html))
    msg.add_alternative(_wrap_html(html), subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            start_tls=settings.SMTP_USE_TLS and settings.SMTP_PORT != 465,
            timeout=10,
        )
        return True, None
    except Exception as exc:
        logger.exception("SMTP send failed")
        return False, f"{exc.__class__.__name__}: {exc}"

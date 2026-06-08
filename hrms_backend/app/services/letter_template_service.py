"""Letter-template renderer + first-boot seeder.

The renderer takes a `LetterTemplate` body that uses ``{{placeholder}}``
markers, substitutes them from the employee context, and produces a
PDF stamped with the Jaikalki letterhead (the same image extracted
from `letter_documents/New Letterhead Jaikalki.docx`).
"""
from __future__ import annotations

import io
import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Employee, LetterTemplate
from app.services.jaikalki_documents import (
    BRAND_BROWN_DARK,
    BRAND_GOLD,
    FONT_BOLD,
    FONT_REGULAR,
    _styles,
)


_log = logging.getLogger(__name__)


def _letterhead_path() -> Optional[Path]:
    """Locate the bundled letterhead PNG (extracted from the .docx)."""
    candidates = []
    override = getattr(settings, "LETTERHEAD_PATH", None)
    if override:
        candidates.append(Path(str(override)))
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.append(parent / "logos" / "jaikalki-letterhead.png")
        candidates.append(parent / "logos" / "jaikalki-app-icon-512.png")
    for p in candidates:
        try:
            if p.exists():
                return p
        except OSError:
            continue
    return None


# ── Placeholder substitution ──────────────────────────────────────────
_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def _salutation(employee: Employee) -> str:
    g = (employee.gender or "").lower()
    if g == "female":
        return "Ms."
    if g == "male":
        return "Mr."
    return "Mr./Ms."


def _context_for(employee: Employee, overrides: Optional[dict]) -> dict:
    today = date.today()
    ctx: dict = {
        "full_name": f"{employee.first_name} {employee.last_name}".strip(),
        "first_name": employee.first_name or "",
        "last_name": employee.last_name or "",
        "salutation": _salutation(employee),
        "employee_code": employee.employee_code or "",
        "designation": (
            employee.designation.name if employee.designation else ""
        ),
        "department": (
            employee.department.name if employee.department else ""
        ),
        "date_of_joining": (
            employee.date_of_joining.strftime("%d %b %Y")
            if employee.date_of_joining
            else ""
        ),
        "email": employee.personal_email or "",
        "phone": employee.personal_phone or "",
        "ctc_amount": (
            f"{int(employee.ctc_annual):,}" if employee.ctc_annual else ""
        ),
        "ctc_amount_words": "",
        "date": today.strftime("%d %b %Y"),
        "address": "",
        "last_working_date": "",
        "letter_no": "",
    }
    if overrides:
        for k, v in overrides.items():
            if v is None:
                continue
            ctx[k] = str(v)
    return ctx


def render_letter_body(body: str, context: dict) -> str:
    """Substitute ``{{key}}`` markers from ``context``. Unknown keys are
    left in place so the admin notices and can either fix the template
    or pass an override."""

    def _sub(m: re.Match[str]) -> str:
        key = m.group(1)
        return str(context.get(key, m.group(0)))

    return _PLACEHOLDER_RE.sub(_sub, body)


# ── PDF render ────────────────────────────────────────────────────────
def _letterhead_decorator(letterhead: Optional[Path]):
    def _draw(canvas, doc):
        canvas.saveState()
        if letterhead is not None:
            try:
                img = ImageReader(str(letterhead))
                iw, ih = img.getSize()
                aspect = (iw / ih) if ih else 1.0
                # Place the letterhead at the top, centred, scaled to fit
                # the full page width minus the side margins.
                page_w, page_h = A4
                target_w = page_w - 3.2 * cm
                target_h = target_w / aspect
                # Cap the height so the letterhead never crashes into
                # the body text.
                max_h = 4 * cm
                if target_h > max_h:
                    target_h = max_h
                    target_w = target_h * aspect
                x = (page_w - target_w) / 2
                y = page_h - target_h - 1.0 * cm
                canvas.drawImage(
                    img,
                    x,
                    y,
                    width=target_w,
                    height=target_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
                # Also stamp a faint watermark in the page centre.
                wm_w = 11 * cm
                wm_h = wm_w / aspect
                canvas.setFillAlpha(0.06)
                canvas.drawImage(
                    img,
                    (page_w - wm_w) / 2,
                    (page_h - wm_h) / 2,
                    width=wm_w,
                    height=wm_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
                canvas.setFillAlpha(1)
            except Exception as exc:  # pragma: no cover
                _log.warning("Letterhead draw failed: %s", exc)

        # Brown footer rule + page number.
        canvas.setStrokeColor(BRAND_GOLD)
        canvas.setLineWidth(0.6)
        canvas.line(1.8 * cm, 1.4 * cm, A4[0] - 1.8 * cm, 1.4 * cm)
        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(colors.dimgray)
        canvas.drawString(
            1.8 * cm, 1 * cm,
            f"{settings.COMPANY_NAME} · Confidential",
        )
        canvas.drawRightString(
            A4[0] - 1.8 * cm, 1 * cm,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    return _draw


def _para(text: str, style) -> Paragraph:
    """ReportLab-friendly paragraph from plain text. Escapes <, &."""
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return Paragraph(safe, style)


def render_letter_pdf(
    template: LetterTemplate,
    employee: Employee,
    *,
    overrides: Optional[dict] = None,
) -> bytes:
    ctx = _context_for(employee, overrides)
    body = render_letter_body(template.body, ctx)
    subject = (
        render_letter_body(template.subject, ctx) if template.subject else None
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=5.0 * cm,   # reserved for letterhead band
        bottomMargin=1.8 * cm,
        title=f"{template.name} · {employee.employee_code}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    # Letter number + date row.
    letter_no = (ctx.get("letter_no") or "").strip()
    if letter_no:
        head = Table(
            [[
                Paragraph(
                    f"<font name='{FONT_BOLD}' color='#2D1810'>{letter_no}</font>",
                    s["body"],
                ),
                Paragraph(
                    f"<font name='{FONT_REGULAR}'>Date: {ctx['date']}</font>",
                    s["right"],
                ),
            ]],
            colWidths=[10 * cm, 7.4 * cm],
        )
        head.setStyle(TableStyle([
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(head)
        story.append(Spacer(1, 10))
    else:
        story.append(_para(f"Date: {ctx['date']}", s["right"]))
        story.append(Spacer(1, 6))

    if subject:
        story.append(_para(f"<b>{subject}</b>", s["body"]))
        story.append(Spacer(1, 8))

    # Body — split on blank lines into paragraphs so spacing reads well.
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Preserve single-line breaks within a paragraph.
        html = chunk.replace("\n", "<br/>")
        # Escape HTML special chars on a per-segment basis then re-add
        # the explicit <br/> markers we inserted above.
        html = (
            html.replace("&", "&amp;")
            .replace("<br/>", "::BR::")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("::BR::", "<br/>")
        )
        story.append(Paragraph(html, s["body"]))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 18))
    story.append(_para("For Jaikalki Technology Pvt Ltd", s["body"]))
    story.append(Spacer(1, 24))
    story.append(_para("__________________________", s["body"]))
    story.append(_para("Authorised Signatory", s["body"]))

    decorator = _letterhead_decorator(_letterhead_path())
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)
    return buffer.getvalue()


# ── Seeding ───────────────────────────────────────────────────────────
async def seed_default_templates(db: AsyncSession) -> int:
    """Insert the bundled HR letter templates if they aren't already on
    the DB. Returns the number of rows added. Safe to call repeatedly."""
    seed_file = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "letter_templates_seed.json"
    )
    if not seed_file.exists():
        return 0
    try:
        rows = json.loads(seed_file.read_text())
    except Exception as exc:
        _log.warning("letter template seed unreadable: %s", exc)
        return 0
    existing = {
        r.code
        for r in (await db.execute(select(LetterTemplate))).scalars().all()
    }
    added = 0
    for r in rows:
        if r["code"] in existing:
            continue
        db.add(
            LetterTemplate(
                code=r["code"],
                name=r["name"],
                category=r.get("category", "other"),
                subject=r.get("subject"),
                body=r["body"],
                placeholders=r.get("placeholders"),
                is_active=True,
            )
        )
        added += 1
    if added:
        await db.commit()
    return added

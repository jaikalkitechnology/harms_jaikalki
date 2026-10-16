"""Letter-template renderer + first-boot seeder.

The renderer takes a `LetterTemplate` body that uses ``{{placeholder}}``
markers, substitutes them from the employee context, and produces a
PDF stamped with the Jaikalki letterhead — designed to match the
official "New Letterhead Jaikalki" reference.
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
from reportlab.lib.units import cm, mm
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
from app.services import storage
from app.services.letterhead import DEFAULTS as LETTERHEAD_DEFAULTS
from app.services.jaikalki_documents import (
    BRAND_BROWN_DARK,
    BRAND_GOLD,
    FONT_BOLD,
    FONT_REGULAR,
    _styles,
)


_log = logging.getLogger(__name__)


# ── Company identity (header / footer text on every letter) ────────────
# Reproduces the official "New Letterhead Jaikalki" reference layout:
# logo · company name · CIN · GST · contact line · regd-office line on
# top; corporate-office block bottom-right; faint sunflower watermark
# in the centre. The text and logo are editable in Settings → Letterhead
# (see app.services.letterhead); these are the defaults.
COMPANY_LEGAL_NAME = LETTERHEAD_DEFAULTS["company_name"]
COMPANY_REGD_OFFICE_PREFIX = "Regd. Office:"


def _letterhead_path() -> Optional[Path]:
    """Faint full-page watermark logo (the big sunflower mark)."""
    candidates: list[Path] = []
    override = getattr(settings, "LETTERHEAD_PATH", None)
    if override:
        candidates.append(Path(str(override)))
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.append(parent / "logos" / "jaikalki-letterhead.png")
    for p in candidates:
        try:
            if p.exists():
                return p
        except OSError:
            continue
    return None


def _icon_path() -> Optional[Path]:
    """Small header logo (left of the company name). Reuses the same
    full Jaikalki mark used for the page watermark so the visual
    identity is consistent — the previous icon-only sunflower didn't
    carry the wordmark."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        for name in (
            "jaikalki-letterhead.png",
            "jaikalki-app-icon-cream-1024.png",
            "jaikalki-app-icon-1024.png",
            "jaikalki-app-icon-512.png",
        ):
            p = parent / "logos" / name
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
_TINTED_BROWN = colors.HexColor("#3D2817")
_HEADER_GOLD = colors.HexColor("#C8941A")
_CORNER_BROWN = colors.HexColor("#2D1810")


def _draw_spaced(canvas, text: str, x: float, y: float, *,
                  font: str, size: float, char_space: float = 0.0,
                  color=_TINTED_BROWN, right: bool = False,
                  center: bool = False) -> None:
    """Draw a string with explicit char-spacing (used for the
    letter-spaced look in the official letterhead). ReportLab applies
    char spacing only through a text object, so we measure width via
    ``stringWidth`` to support right-alignment."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    if right or center:
        # Compute total width including the added char spacing.
        w = stringWidth(text, font, size) + char_space * max(0, len(text) - 1)
        start = x - (w / 2 if center else w)
    else:
        start = x
    text_obj = canvas.beginText(start, y)
    text_obj.setFont(font, size)
    text_obj.setFillColor(color)
    text_obj.setCharSpace(char_space)
    text_obj.textOut(text)
    canvas.drawText(text_obj)


def _wrap_spaced(
    text: str, font: str, size: float, char_space: float, width: float
) -> list[str]:
    """Word-wrap for letter-spaced text (``simpleSplit`` ignores the
    extra char spacing)."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    def w(t: str) -> float:
        return stringWidth(t, font, size) + char_space * max(0, len(t) - 1)

    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and w(trial) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _image(source) -> Optional[ImageReader]:
    if source is None:
        return None
    try:
        if isinstance(source, (bytes, bytearray)):
            return ImageReader(io.BytesIO(bytes(source)))
        return ImageReader(str(source))
    except Exception as exc:  # pragma: no cover — bad upload
        _log.warning("Letterhead logo unreadable: %s", exc)
        return None


def letterhead_images(letterhead: Optional[dict]):
    """(watermark, header logo) for a letterhead config. An uploaded logo
    replaces both; otherwise the bundled Jaikalki marks are used."""
    key = (letterhead or {}).get("logo_key")
    if key:
        try:
            img = _image(storage.read_bytes(key))
            if img is not None:
                return img, img
        except Exception as exc:
            _log.warning("Letterhead logo %s missing: %s", key, exc)
    return _image(_letterhead_path()), _image(_icon_path())


def _letterhead_decorator(
    watermark: Optional[ImageReader],
    icon: Optional[ImageReader],
    letterhead: Optional[dict] = None,
):
    """Returns a canvas callback that renders the letterhead (header +
    watermark + footer) on every page, from the Settings → Letterhead
    values in ``letterhead`` (defaults when None)."""
    lh = {**LETTERHEAD_DEFAULTS, **(letterhead or {})}

    def _draw(canvas, doc):
        canvas.saveState()
        page_w, page_h = A4

        # ── Decorative corner shapes ──────────────────────────────
        # Small dark-brown triangles in two opposing corners. Kept
        # compact so they never clip the company-info text.
        if lh.get("show_corner_accents", True):
            canvas.setFillColor(_CORNER_BROWN)
            canvas.setStrokeColor(_CORNER_BROWN)
            # Top-right
            p = canvas.beginPath()
            p.moveTo(page_w, page_h)
            p.lineTo(page_w - 2.4 * cm, page_h)
            p.lineTo(page_w, page_h - 1.8 * cm)
            p.close()
            canvas.drawPath(p, fill=1, stroke=0)
            # Bottom-left — tiny accent only, so the confidentiality
            # line and page number both clear the brown wedge.
            p = canvas.beginPath()
            p.moveTo(0, 0)
            p.lineTo(1.2 * cm, 0)
            p.lineTo(0, 0.7 * cm)
            p.close()
            canvas.drawPath(p, fill=1, stroke=0)

        # ── Centre watermark (faint full logo) ────────────────────
        if watermark is not None and lh.get("show_watermark", True):
            try:
                iw, ih = watermark.getSize()
                aspect = (iw / ih) if ih else 1.0
                wm_w = 12 * cm
                wm_h = wm_w / aspect
                if wm_h > 14 * cm:  # tall logos: cap the height
                    wm_h = 14 * cm
                    wm_w = wm_h * aspect
                canvas.setFillAlpha(0.08)
                canvas.drawImage(
                    watermark,
                    (page_w - wm_w) / 2,
                    (page_h - wm_h) / 2,
                    width=wm_w,
                    height=wm_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
                canvas.setFillAlpha(1)
            except Exception as exc:  # pragma: no cover
                _log.warning("Watermark draw failed: %s", exc)

        # ── Header band ───────────────────────────────────────────
        margin = 1.8 * cm
        top = page_h - 1.0 * cm
        # Logo top-left, in a 3 cm × 1.8 cm box (aspect preserved).
        icon_w = 3.0 * cm
        icon_h = 1.8 * cm
        if icon is not None:
            try:
                canvas.drawImage(
                    icon,
                    margin,
                    top - icon_h,
                    width=icon_w,
                    height=icon_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
            except Exception:  # pragma: no cover
                icon_w = 0
        else:
            icon_w = 0

        # Company name + identifiers, right of the logo
        text_x = margin + (icon_w + 0.5 * cm if icon_w else 0)
        right_x = page_w - margin
        name = (lh.get("company_name") or "").strip()
        if name:
            # Shrink long names so they stay on one line.
            from reportlab.pdfbase.pdfmetrics import stringWidth

            size = 13.5
            avail = right_x - text_x
            while size > 8 and (
                stringWidth(name, FONT_BOLD, size) + 1.2 * len(name) > avail
            ):
                size -= 0.5
            _draw_spaced(
                canvas, name,
                text_x, top - 0.6 * cm,
                font=FONT_BOLD, size=size, char_space=1.2,
                color=_TINTED_BROWN,
            )
        # CIN + GST right-aligned, letter-spaced
        ids = [
            f"{label}: {lh[k]}"
            for label, k in (("CIN", "cin"), ("GST", "gst"))
            if (lh.get(k) or "").strip()
        ]
        for i, line in enumerate(ids):
            _draw_spaced(
                canvas, line,
                right_x, top - (1.1 + 0.45 * i) * cm,
                font=FONT_BOLD, size=8.5, char_space=1.0,
                color=_TINTED_BROWN, right=True,
            )

        # Contact row (phone | email | web) — centred mid-band
        contact = "    |    ".join(
            f"{sym}  {lh[k]}".strip()
            for sym, k in (("☎", "phone"), ("✉", "email"), ("", "website"))
            if (lh.get(k) or "").strip()
        )
        if contact:
            _draw_spaced(
                canvas, contact, page_w / 2, top - 2.15 * cm,
                font=FONT_REGULAR, size=9, char_space=0.6,
                color=_TINTED_BROWN, center=True,
            )

        # Gold rule under the header
        canvas.setStrokeColor(_HEADER_GOLD)
        canvas.setLineWidth(0.8)
        canvas.line(margin, top - 2.5 * cm, page_w - margin, top - 2.5 * cm)

        # Regd. office address — wrapped to at most two centred lines so
        # it can't bleed past the usable width.
        regd = (lh.get("regd_office") or "").strip()
        if regd:
            for i, line in enumerate(
                _wrap_spaced(
                    f"{COMPANY_REGD_OFFICE_PREFIX} {regd}",
                    FONT_BOLD, 7.5, 0.6, page_w - 2 * margin,
                )[:2]
            ):
                _draw_spaced(
                    canvas, line, page_w / 2, top - (2.95 + 0.4 * i) * cm,
                    font=FONT_BOLD, size=7.5, char_space=0.6,
                    color=_TINTED_BROWN, center=True,
                )

        # ── Footer corporate-office block (bottom-right) ───────────
        foot_x = page_w - margin
        foot_y = 4.6 * cm
        office = [
            ln.strip()
            for ln in (lh.get("corporate_office") or "").splitlines()
            if ln.strip()
        ][:7]
        for i, line in enumerate(office):
            _draw_spaced(
                canvas, line, foot_x, foot_y - i * 0.45 * cm,
                font=FONT_BOLD if i == 0 else FONT_REGULAR,
                size=9 if i == 0 else 8.5,
                char_space=1.2,
                color=_TINTED_BROWN,
                right=True,
            )

        # ── Bottom rule + footer note + page number ──────────────
        canvas.setStrokeColor(_HEADER_GOLD)
        canvas.setLineWidth(0.6)
        canvas.line(margin, 1.5 * cm, page_w - margin, 1.5 * cm)
        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(colors.dimgray)
        canvas.drawString(
            margin, 1.0 * cm,
            (lh.get("footer_note") or "").strip()
            or f"{settings.COMPANY_NAME} · Confidential",
        )
        canvas.drawRightString(
            page_w - margin, 1.0 * cm,
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
    letterhead: Optional[dict] = None,
) -> bytes:
    ctx = _context_for(employee, overrides)
    body = render_letter_body(template.body, ctx)
    subject = (
        render_letter_body(template.subject, ctx) if template.subject else None
    )
    # Templates that already print {{letter_no}} / {{date}} in the body
    # don't get them repeated in the row above it.
    used = set(_PLACEHOLDER_RE.findall(template.body))
    return build_letter_pdf(
        title=f"{template.name} · {employee.employee_code}",
        subject=subject,
        body=body,
        letter_no="" if "letter_no" in used else (ctx.get("letter_no") or ""),
        on_date="" if "date" in used else ctx["date"],
        letterhead=letterhead,
    )


def build_letter_pdf(
    *,
    title: str,
    subject: Optional[str],
    body: str,
    letter_no: str = "",
    on_date: str = "",
    letterhead: Optional[dict] = None,
) -> bytes:
    """Lay out an already-filled letter on the letterhead."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        # Reserved space for the company header band on every page.
        topMargin=5.6 * cm,
        # Reserved space for the corporate-office footer block + rule.
        bottomMargin=6.0 * cm,
        title=title,
        author=(letterhead or {}).get("company_name") or settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    # Letter number + date row.
    letter_no = (letter_no or "").strip()
    if letter_no:
        head = Table(
            [[
                Paragraph(
                    f"<font name='{FONT_BOLD}' color='#2D1810'>{letter_no}</font>",
                    s["body"],
                ),
                Paragraph(
                    f"<font name='{FONT_REGULAR}'>Date: {on_date}</font>"
                    if on_date else "",
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
    elif on_date:
        story.append(_para(f"Date: {on_date}", s["right"]))
        story.append(Spacer(1, 6))

    if subject:
        safe_subject = (
            subject.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        story.append(Paragraph(f"<b>{safe_subject}</b>", s["body"]))
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

    # Templates carry their own sign-off ("For Jaikalki ..." / "Director"
    # / signature lines), so nothing extra is appended here.

    watermark, icon = letterhead_images(letterhead)
    decorator = _letterhead_decorator(watermark, icon, letterhead)
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)
    return buffer.getvalue()


def render_letterhead_preview(letterhead: dict) -> bytes:
    """A sample letter showing how the letterhead will look."""
    return build_letter_pdf(
        title="Letterhead preview",
        subject="Subject: Letterhead preview",
        body=(
            "Dear Employee,\n\n"
            "This is a sample letter showing the company letterhead — the "
            "logo, company name, registration numbers and contact line at "
            "the top, and the office address and footer note at the "
            "bottom. Every letter generated from a template is printed on "
            "this letterhead.\n\n"
            "Regards,\nHR Department"
        ),
        letter_no="JKT/HR/2026/0001",
        on_date=date.today().strftime("%d %b %Y"),
        letterhead=letterhead,
    )


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

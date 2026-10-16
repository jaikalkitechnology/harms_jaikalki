"""Jaikalki PDF document generators.

Headline output: an offer letter that reproduces the format used in
JKT/HR/AL/014/2025 (Pooja Kumawat, JKT014). Uses reportlab so it ships
without any external font / browser dependency.

The Annexure A pulls live numbers from JaikalkiSalaryCalculator so a
fresh offer letter for an employee on the same template prints the same
breakup as their offer-letter run.
"""
from __future__ import annotations

import io
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Employee, EmployeeBankDetails, GeneratedDocument, Payslip, User
from app.services.salary_calculator import JaikalkiSalaryCalculator
from app.services.storage import upload_fileobj


BRAND_BROWN = colors.HexColor("#3D2817")
BRAND_BROWN_DARK = colors.HexColor("#2D1810")
BRAND_GOLD = colors.HexColor("#C8941A")
BRAND_GOLD_LIGHT = colors.HexColor("#F4B71F")
BRAND_BG = colors.HexColor("#FDF8EE")
GRID = colors.HexColor("#E8DACA")


_log = logging.getLogger(__name__)

# ── Unicode font (so the rupee symbol renders) ─────────────────────────
# Helvetica (reportlab's default) has no glyph for ₹ and prints a box.
# Try a couple of well-known TTFs; fall back to a "Rs." prefix when none
# are installed on the host so the PDF still reads cleanly.
_FONT_CANDIDATES = [
    (
        "DejaVuSans",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "NotoSans",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ),
]


def _register_unicode_font() -> Optional[str]:
    for name, reg, bold in _FONT_CANDIDATES:
        try:
            if Path(reg).exists() and Path(bold).exists():
                pdfmetrics.registerFont(TTFont(name, reg))
                pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                from reportlab.pdfbase.pdfmetrics import registerFontFamily

                registerFontFamily(
                    name,
                    normal=name,
                    bold=f"{name}-Bold",
                    italic=name,
                    boldItalic=f"{name}-Bold",
                )
                return name
        except Exception as exc:  # pragma: no cover
            _log.warning("Could not register font %s: %s", name, exc)
    return None


_UNICODE_FONT = _register_unicode_font()
FONT_REGULAR = _UNICODE_FONT or "Helvetica"
FONT_BOLD = f"{_UNICODE_FONT}-Bold" if _UNICODE_FONT else "Helvetica-Bold"
RUPEE = "₹" if _UNICODE_FONT else "Rs."


def _logo_path() -> Optional[Path]:
    """Locate the Jaikalki app logo bundled with the repo. Looked up at
    render-time so the file isn't required to be on the import path."""
    # Allow override via settings (env), then fall back to repo defaults.
    override = getattr(settings, "PAYSLIP_LOGO_PATH", None)
    candidates = []
    if override:
        candidates.append(Path(str(override)))
    here = Path(__file__).resolve()
    for up in (here.parents[3], here.parents[2], here.parents[4] if len(here.parents) > 4 else here.parents[3]):
        candidates.append(up / "logos" / "jaikalki-app-icon-512.png")
        candidates.append(up / "logos" / "jaikalki-icon-only-512.png")
    for p in candidates:
        try:
            if p.exists():
                return p
        except OSError:
            continue
    return None



# ── Letter number sequencing ────────────────────────────────────────
async def _next_letter_number(
    db: AsyncSession, *, doc_type: str, year: int
) -> str:
    """JKT/HR/AL/{seq}/{year} for offer letters, JKT/HR/CL/{seq}/{year} for
    confirmation letters — same sequence as letters issued from templates."""
    from app.services.letter_numbers import next_letter_number

    return await next_letter_number(
        db, "offer" if doc_type == "offer_letter" else "confirmation", year
    )


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s = {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName=FONT_BOLD,
            fontSize=18, leading=22, textColor=BRAND_BROWN_DARK,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName=FONT_BOLD,
            fontSize=12, leading=15, spaceBefore=10, spaceAfter=4,
            textColor=BRAND_BROWN_DARK,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName=FONT_REGULAR,
            fontSize=10, leading=14, alignment=4, textColor=BRAND_BROWN_DARK,
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"], fontName=FONT_REGULAR,
            fontSize=9, leading=12, textColor=colors.dimgray,
        ),
        "right": ParagraphStyle(
            "right", parent=base["BodyText"], fontName=FONT_REGULAR,
            fontSize=10, leading=13, alignment=2, textColor=BRAND_BROWN_DARK,
        ),
        "label": ParagraphStyle(
            "label", parent=base["BodyText"], fontName="Helvetica-Oblique",
            fontSize=9, leading=11, textColor=BRAND_GOLD,
        ),
        "company": ParagraphStyle(
            "company", parent=base["Title"], fontName=FONT_BOLD,
            fontSize=20, leading=22, textColor=BRAND_BROWN_DARK, alignment=1,
        ),
    }
    return s


# ── Offer letter ──────────────────────────────────────────────────────
async def generate_offer_letter(
    db: AsyncSession,
    employee: Employee,
    *,
    generated_by: Optional[User] = None,
    upload_to_storage: bool = True,
    on_date: Optional[date] = None,
) -> tuple[bytes, GeneratedDocument]:
    if not employee.salary_template:
        raise ValidationError(
            "Employee has no salary template — cannot generate offer letter"
        )

    letter_date = on_date or date.today()
    letter_no = await _next_letter_number(
        db, doc_type="offer_letter", year=letter_date.year
    )
    from app.services.pf_ceiling_service import cap_on

    pf_cap, _eps = await cap_on(db, letter_date)
    breakup = JaikalkiSalaryCalculator().calculate(
        employee.salary_template,
        ctc_annual=employee.ctc_annual or None,
        employee=employee,
        pf_cap=pf_cap,
    ).as_dict()

    from app.services.letterhead import get_letterhead

    pdf_bytes = _render_offer_letter(
        employee,
        letter_no=letter_no,
        on_date=letter_date,
        breakup=breakup,
        letterhead=await get_letterhead(db),
    )

    file_url = ""
    if upload_to_storage:
        try:
            _, file_url = upload_fileobj(
                io.BytesIO(pdf_bytes),
                key_prefix=f"offer-letters/{employee.employee_code}",
                filename=f"{letter_no.replace('/', '_')}.pdf",
                content_type="application/pdf",
            )
        except Exception:
            # MinIO not reachable in some environments — keep the bytes
            # so the test can still consume them. file_url stays empty.
            file_url = ""

    doc = GeneratedDocument(
        employee_id=employee.id,
        doc_type="offer_letter",
        letter_number=letter_no,
        file_url=file_url or f"local://offer-letters/{letter_no}.pdf",
        payload={
            "breakup": breakup,
            "ctc_annual": str(employee.ctc_annual or 0),
            "letter_date": letter_date.isoformat(),
        },
        generated_by=generated_by.id if generated_by else None,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return pdf_bytes, doc


def _render_offer_letter(
    employee: Employee,
    *,
    letter_no: str,
    on_date: date,
    breakup: dict,
    letterhead: Optional[dict] = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        # Room for the letterhead header band and footer office block.
        topMargin=5.6 * cm,
        bottomMargin=6.0 * cm,
        title=f"Offer Letter · {employee.employee_code}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    # Company name and address come from the letterhead.

    # Letter number + date row
    meta = Table(
        [[Paragraph(letter_no, s["body"]),
          Paragraph(f"Date: {on_date.strftime('%d %b %Y')}", s["right"])]],
        colWidths=[10 * cm, 7 * cm],
    )
    meta.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(meta)
    story.append(Spacer(1, 8))

    # ── Address block ────────────────────────────────────────────────
    name_line = (
        f"{_salutation(employee)} {employee.first_name} {employee.last_name},"
    )
    story.append(Paragraph(name_line, s["body"]))
    story.append(Paragraph(f"Emp. Code: {employee.employee_code}", s["body"]))
    if employee.personal_email:
        story.append(Paragraph(employee.personal_email, s["small"]))
    story.append(Spacer(1, 14))

    # ── Subject ──────────────────────────────────────────────────────
    story.append(Paragraph("<b>Subject: Appointment Letter</b>", s["body"]))
    story.append(Spacer(1, 8))

    salutation = (
        f"Dear {'Ms.' if (employee.gender or '').lower() == 'female' else 'Mr.'} "
        f"{employee.first_name},"
    )
    story.append(Paragraph(salutation, s["body"]))
    story.append(Spacer(1, 6))

    intro = (
        f"With reference to your application and subsequent interviews held with "
        f"the management of <b>{settings.COMPANY_NAME}</b> ('the Company'), we are "
        f"pleased to offer you the position of "
        f"<b>{employee.designation.name if employee.designation else 'Employee'}</b> "
        f"on the following terms and conditions:"
    )
    story.append(Paragraph(intro, s["body"]))
    story.append(Spacer(1, 8))

    # ── Body sections ────────────────────────────────────────────────
    for heading, body in _body_sections(employee, breakup):
        story.append(Paragraph(heading, s["h1"]))
        for para in body:
            story.append(Paragraph(para, s["body"]))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "We welcome you to the <b>Jaikalki</b> family and look forward to a long "
        "and rewarding association.",
        s["body"],
    ))
    story.append(Spacer(1, 24))

    # ── Signature block ──────────────────────────────────────────────
    sig = Table(
        [
            ["For Jaikalki Technology Pvt Ltd", "Accepted by"],
            ["", ""],
            ["__________________________", "__________________________"],
            ["Authorised Signatory", f"{employee.first_name} {employee.last_name}"],
        ],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    sig.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT_REGULAR, 10),
        ("FONT", (0, 0), (-1, 0), FONT_BOLD, 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig)

    # ── Annexure A ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Annexure 'A'", s["title"]))
    story.append(Paragraph(
        f"w.e.f. {(employee.date_of_joining or on_date).strftime('%d %b %Y')}",
        s["label"],
    ))
    story.append(Spacer(1, 10))

    info_rows = [
        ["Name", f"{employee.first_name} {employee.last_name}"],
        [
            "Designation",
            employee.designation.name if employee.designation else "—",
        ],
        [
            "Department",
            employee.department.name if employee.department else "—",
        ],
        ["Employee Code", employee.employee_code],
        ["Category", employee.category.name if employee.category else "—"],
    ]
    info = Table(info_rows, colWidths=[5 * cm, 12 * cm])
    info.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT_REGULAR, 10),
        ("FONT", (0, 0), (0, -1), FONT_BOLD, 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, GRID),
        ("BACKGROUND", (0, 0), (0, -1), BRAND_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(info)
    story.append(Spacer(1, 12))

    # Salary table
    story.append(Paragraph("Salary Compensation Structure", s["h1"]))
    story.append(_salary_table(breakup))
    story.append(Spacer(1, 12))

    # Insurance benefits
    insurance_total = (
        Decimal(employee.salary_template.mediclaim_amount or 0)
        + Decimal(employee.salary_template.pa_insurance_amount or 0)
    )
    story.append(Paragraph("Insurance Benefits", s["h1"]))
    insurance_rows = [
        ["Group Mediclaim", f"{RUPEE}{int(employee.salary_template.mediclaim_amount or 0):,}"],
        [
            "Group Personal Accident",
            f"{RUPEE}{int(employee.salary_template.pa_insurance_amount or 0):,}",
        ],
        ["Total Insurance", f"{RUPEE}{int(insurance_total):,}"],
    ]
    ins = Table(insurance_rows, colWidths=[10 * cm, 7 * cm])
    ins.setStyle(_table_style(highlight_last=True))
    story.append(ins)

    page = _letterhead_page(letterhead)
    doc.build(story, onFirstPage=page, onLaterPages=page)
    return buffer.getvalue()


def _salary_table(breakup: dict, *, show_annual: bool = True) -> Table:
    def fmt(n: int) -> str:
        return f"{RUPEE} {int(n):,}"

    if show_annual:
        rows: list = [
            ["Component", f"Per Month ({RUPEE})", f"Per Annum ({RUPEE})"]
        ]
    else:
        rows = [["Component", f"Per Month ({RUPEE})"]]

    def row(label: str, monthly: int) -> list:
        return (
            [label, fmt(monthly), fmt(monthly * 12)]
            if show_annual
            else [label, fmt(monthly)]
        )

    section_pad = ["", "", ""] if show_annual else ["", ""]

    earnings_rows = [
        ("Basic Salary", "basic"),
        ("House Rent Allowance (HRA)", "hra"),
        ("Other Allowance", "other_allowance"),
        ("Special Allowance", "special_allowance"),
        ("Conveyance", "conveyance"),
        ("Medical Allowance", "medical_allowance"),
        ("LTA", "lta"),
        ("Food Coupon", "food_coupon"),
    ]
    rows.append(["EARNINGS", *section_pad[1:]])
    for label, key in earnings_rows:
        v = int(breakup.get(key, 0) or 0)
        if v <= 0:
            continue
        rows.append(row(label, v))
    rows.append(row("Gross Salary", int(breakup["gross"])))

    rows.append(["EMPLOYEE DEDUCTIONS", *section_pad[1:]])
    rows.append(row("Provident Fund (Employee)", int(breakup["pf_employee"])))
    rows.append(row("ESIC (Employee)", int(breakup["esic_employee"])))
    rows.append(row("Professional Tax", int(breakup["professional_tax"])))
    rows.append(row("Total Deductions", int(breakup["total_deductions"])))

    rows.append(row("Net Salary", int(breakup["net_salary"])))

    rows.append(["EMPLOYER CONTRIBUTIONS", *section_pad[1:]])
    rows.append(row("Provident Fund (Employer)", int(breakup["pf_employer"])))
    rows.append(row("ESIC (Employer)", int(breakup["esic_employer"])))

    if show_annual:
        rows.append([
            "TOTAL CTC",
            fmt(int(breakup["total_ctc_monthly"])),
            fmt(int(breakup["total_ctc_annual"])),
        ])
    else:
        rows.append([
            "TOTAL CTC",
            fmt(int(breakup["total_ctc_monthly"])),
        ])

    if show_annual:
        t = Table(rows, colWidths=[8 * cm, 4.5 * cm, 4.5 * cm])
    else:
        t = Table(rows, colWidths=[11.5 * cm, 5.5 * cm])

    # Locate the visual "section" rows so we can colour them.
    section_idx = [
        i for i, r in enumerate(rows)
        if r[0] in ("EARNINGS", "EMPLOYEE DEDUCTIONS", "EMPLOYER CONTRIBUTIONS")
    ]
    bold_idx = [
        i for i, r in enumerate(rows)
        if r[0] in (
            "Gross Salary", "Total Deductions", "Net Salary", "TOTAL CTC"
        )
    ]
    style_cmds = [
        ("FONT", (0, 0), (-1, -1), FONT_REGULAR, 9),
        ("FONT", (0, 0), (-1, 0), FONT_BOLD, 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BROWN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, GRID),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in section_idx:
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), BRAND_BG))
        style_cmds.append(("FONT", (0, i), (-1, i), FONT_BOLD, 9))
        style_cmds.append(("SPAN", (0, i), (-1, i)))
    for i in bold_idx:
        style_cmds.append(("FONT", (0, i), (-1, i), FONT_BOLD, 9))
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBF6E9")))
    # CTC row: gold accent
    if rows[-1][0] == "TOTAL CTC":
        last = len(rows) - 1
        style_cmds.append(("BACKGROUND", (0, last), (-1, last), BRAND_GOLD))
        style_cmds.append(("TEXTCOLOR", (0, last), (-1, last), colors.whitesmoke))

    t.setStyle(TableStyle(style_cmds))
    return t


def _table_style(highlight_last: bool = False) -> TableStyle:
    cmds = [
        ("FONT", (0, 0), (-1, -1), FONT_REGULAR, 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, GRID),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if highlight_last:
        cmds.append(("FONT", (0, -1), (-1, -1), FONT_BOLD, 10))
        cmds.append(
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FBF6E9"))
        )
    return TableStyle(cmds)


def _letterhead_page(letterhead: Optional[dict]):
    """Page callback drawing the company letterhead from Settings →
    Letterhead — the same one template letters use."""
    # Imported here: letter_template_service imports from this module.
    from app.services.letter_template_service import (
        _letterhead_decorator,
        letterhead_images,
    )

    watermark, icon = letterhead_images(letterhead)
    return _letterhead_decorator(watermark, icon, letterhead)


def _salutation(employee: Employee) -> str:
    g = (employee.gender or "").lower()
    if g == "female":
        return "Ms."
    if g == "male":
        return "Mr."
    return "Mr./Ms."


def _body_sections(employee: Employee, breakup: dict) -> list[tuple[str, list[str]]]:
    template = employee.salary_template
    probation_months = (
        template.probation_months if template and template.has_probation else 0
    )
    notice_prob = template.notice_period_probation if template else 15
    notice_conf = template.notice_period_confirmed if template else 30
    notice_term = template.notice_period_termination if template else 7

    sections: list[tuple[str, list[str]]] = []

    sections.append((
        "1. REMUNERATION",
        [
            (
                "You will be paid a total CTC of "
                f"<b>{RUPEE}{breakup['total_ctc_annual']:,} per annum</b> "
                f"({RUPEE}{breakup['total_ctc_monthly']:,} per month). The detailed "
                "compensation structure is set out in <b>Annexure 'A'</b>."
            ),
            (
                "Your salary will be credited to your designated bank account on "
                "or before the 7th of every month, after deducting applicable "
                "statutory contributions and taxes."
            ),
        ],
    ))
    sections.append((
        "2. CONFIDENTIALITY",
        [
            (
                "You shall keep all information regarding the Company, its clients "
                "and its operations strictly confidential, both during and after "
                "your employment, and shall not disclose or use such information "
                "for any purpose other than your duties at Jaikalki."
            ),
        ],
    ))
    sections.append((
        "3. ASSIGNMENT",
        [
            (
                "Any work product, intellectual property or invention created by "
                "you in the course of your employment shall be the sole property "
                "of the Company."
            ),
        ],
    ))
    if probation_months:
        sections.append((
            "4. PROBATION & CONFIRMATION",
            [
                (
                    f"You will be on probation for a period of <b>{probation_months} "
                    "months</b> from your date of joining. Probation may be extended "
                    "by up to two months at the Company's discretion based on your "
                    "performance review."
                ),
                (
                    "Upon successful completion of probation, you will be issued a "
                    "written confirmation letter and your service shall be confirmed."
                ),
            ],
        ))
    sections.append((
        "5. PLACE OF POSTING",
        [
            (
                f"Your initial place of posting will be <b>"
                f"{employee.work_location or 'Mira Road, Thane'}</b>. The Company "
                "reserves the right to transfer you to any of its offices, "
                "branches or sites in India as may be required by business needs."
            ),
        ],
    ))
    sections.append((
        "6. RESPONSIBILITY",
        [
            (
                "You will perform the duties assigned to you to the best of your "
                "abilities and devote your whole time and attention to the "
                "business of the Company. You will report to the manager assigned "
                "to you, and abide by the policies of the Company in force from "
                "time to time."
            ),
        ],
    ))
    sections.append((
        "7. VISITS & TRAVEL",
        [
            (
                "You may be required to travel within or outside India in "
                "connection with the Company's work. Travel and lodging will be "
                "reimbursed as per the Company's travel policy."
            ),
        ],
    ))
    sections.append((
        "8. LEAVE",
        [
            (
                "Leave will be governed by the Company's leave policy as amended "
                "from time to time, including casual leave, sick leave, privilege "
                "leave (post-confirmation) and statutory leaves."
            ),
        ],
    ))
    sections.append((
        "9. COMPENSATION PROGRESSION",
        [
            (
                "Your compensation may be reviewed annually based on individual "
                "performance, the Company's performance and prevailing business "
                "conditions. Such review does not create any contractual right "
                "to a salary increase."
            ),
        ],
    ))
    sections.append((
        "10. SEPARATION",
        [
            (
                f"During probation, either party may terminate this employment by "
                f"giving <b>{notice_prob} days</b> written notice. After "
                f"confirmation, the notice period will be <b>{notice_conf} days</b>. "
                f"In case of termination by the Company for misconduct or "
                f"unsatisfactory performance, only <b>{notice_term} days</b> notice "
                "may be given."
            ),
        ],
    ))
    sections.append((
        "11. RETIREMENT",
        [
            (
                "Your retirement age will be <b>58 years</b> unless extended by "
                "the Company in its sole discretion."
            ),
        ],
    ))
    sections.append((
        "12. SETTLEMENT OF DUES",
        [
            (
                "On separation from the Company, your full and final settlement "
                "shall be processed within 30 working days, subject to the return "
                "of all Company property and clearance from all departments."
            ),
        ],
    ))
    sections.append((
        "13. GENERAL",
        [
            (
                "This appointment is subject to verification of your background, "
                "qualifications, references and any documents submitted by you. "
                "The Company reserves the right to revoke this offer in case of "
                "any discrepancy. Your employment shall otherwise be governed by "
                "the standing orders, rules and policies of the Company in force."
            ),
        ],
    ))

    return sections


# ── Confirmation letter ───────────────────────────────────────────────
async def generate_confirmation_letter(
    db: AsyncSession,
    employee: Employee,
    *,
    generated_by: Optional[User] = None,
    upload_to_storage: bool = True,
    on_date: Optional[date] = None,
    confirm: bool = True,
) -> tuple[bytes, GeneratedDocument]:
    letter_date = on_date or date.today()
    letter_no = await _next_letter_number(
        db, doc_type="confirmation_letter", year=letter_date.year
    )

    from app.services.letterhead import get_letterhead

    pdf_bytes = _render_confirmation_letter(
        employee,
        letter_no=letter_no,
        on_date=letter_date,
        letterhead=await get_letterhead(db),
    )

    file_url = ""
    if upload_to_storage:
        try:
            _, file_url = upload_fileobj(
                io.BytesIO(pdf_bytes),
                key_prefix=f"confirmation-letters/{employee.employee_code}",
                filename=f"{letter_no.replace('/', '_')}.pdf",
                content_type="application/pdf",
            )
        except Exception:
            file_url = ""

    doc = GeneratedDocument(
        employee_id=employee.id,
        doc_type="confirmation_letter",
        letter_number=letter_no,
        file_url=file_url or f"local://confirmation-letters/{letter_no}.pdf",
        payload={"letter_date": letter_date.isoformat()},
        generated_by=generated_by.id if generated_by else None,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Generating the confirmation letter also confirms the employee:
    # set confirmation_date + probation_end_date to the letter date and
    # mark the active probation record confirmed. Skipped only when an
    # explicit confirm=False is passed (e.g. a reprint). Idempotent —
    # if there's no active probation we just attach the letter URL.
    if confirm:
        from app.services import employee_service as _emp_svc

        try:
            p = await _emp_svc.get_active_probation(db, employee.id)
            if p is not None:
                await _emp_svc.confirm_employee(
                    db,
                    employee,
                    by_user=generated_by,
                    confirmation_letter_url=doc.file_url,
                    on_date=letter_date,
                )
            else:
                # Already confirmed (or never on probation) — keep the
                # confirmation date in sync with the letter and stamp
                # the URL on the existing probation row if present.
                employee.is_on_probation = False
                if employee.confirmation_date is None:
                    employee.confirmation_date = letter_date
                    employee.probation_end_date = (
                        employee.probation_end_date or letter_date
                    )
                await db.commit()
                await db.refresh(employee)
        except Exception:
            # Never let a confirmation-state hiccup lose the generated
            # PDF; the letter row is already committed above.
            await db.rollback()

    return pdf_bytes, doc


def _render_confirmation_letter(
    employee: Employee,
    *,
    letter_no: str,
    on_date: date,
    letterhead: Optional[dict] = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        # Room for the letterhead header band and footer office block.
        topMargin=5.6 * cm,
        bottomMargin=6.0 * cm,
        title=f"Confirmation Letter · {employee.employee_code}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    # Company name and address come from the letterhead.

    meta = Table(
        [[Paragraph(letter_no, s["body"]),
          Paragraph(f"Date: {on_date.strftime('%d %b %Y')}", s["right"])]],
        colWidths=[10 * cm, 7 * cm],
    )
    meta.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(meta)
    story.append(Spacer(1, 8))

    name_line = (
        f"{_salutation(employee)} {employee.first_name} {employee.last_name},"
    )
    story.append(Paragraph(name_line, s["body"]))
    story.append(Paragraph(f"Emp. Code: {employee.employee_code}", s["body"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "<b>Subject: Confirmation of Employment</b>", s["body"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"Dear {employee.first_name},", s["body"]
    ))
    story.append(Spacer(1, 6))

    body = [
        (
            "We are pleased to inform you that based on your performance during "
            "the probation period, your services with "
            f"<b>{settings.COMPANY_NAME}</b> have been confirmed effective "
            f"<b>{on_date.strftime('%d %b %Y')}</b>."
        ),
        (
            "Your designation, department and current compensation structure "
            "remain unchanged. The notice period from this date onwards will be "
            "<b>30 days</b> as per Company policy."
        ),
        (
            "You will now be eligible for Privilege Leave (PL) as per the Leave "
            "Policy, in addition to all other benefits applicable to confirmed "
            "employees of the Company."
        ),
        (
            "We thank you for your contributions during the probation period and "
            "look forward to your continued contribution to the growth of the "
            "Company."
        ),
    ]
    for p in body:
        story.append(Paragraph(p, s["body"]))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 24))
    sig = Table(
        [
            ["For Jaikalki Technology Pvt Ltd"],
            [""],
            ["__________________________"],
            ["HR Manager"],
        ],
        colWidths=[8 * cm],
    )
    sig.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT_REGULAR, 10),
        ("FONT", (0, 0), (-1, 0), FONT_BOLD, 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig)

    page = _letterhead_page(letterhead)
    doc.build(story, onFirstPage=page, onLaterPages=page)
    return buffer.getvalue()


# ── Payslip PDF ───────────────────────────────────────────────────────
_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _mask_account(acct: Optional[str]) -> str:
    if not acct:
        return "—"
    digits = "".join(ch for ch in acct if ch.isalnum())
    if len(digits) <= 4:
        return digits
    return f"XXXX{digits[-4:]}"


def _make_payslip_page(logo_path: Optional[Path]):
    """Returns a canvas decorator that draws a faint logo watermark and
    a branded footer on every page of the payslip."""

    def _decorate(canvas, doc):
        canvas.saveState()
        # Watermark — large, faint logo behind the content.
        if logo_path is not None:
            try:
                img = ImageReader(str(logo_path))
                iw, ih = img.getSize()
                aspect = iw / ih if ih else 1
                wm_w = 11 * cm
                wm_h = wm_w / aspect
                page_w, page_h = A4
                x = (page_w - wm_w) / 2
                y = (page_h - wm_h) / 2
                canvas.setFillAlpha(0.06)
                canvas.drawImage(
                    img,
                    x,
                    y,
                    width=wm_w,
                    height=wm_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
                canvas.setFillAlpha(1)
            except Exception as exc:  # pragma: no cover
                _log.warning("Watermark draw failed: %s", exc)
        # Footer rule + text
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

    return _decorate


def render_payslip_pdf(
    payslip: Payslip,
    employee: Employee,
    *,
    bank: Optional[EmployeeBankDetails] = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.8 * cm,
        title=f"Payslip · {employee.employee_code} · "
              f"{payslip.month:02d}/{payslip.year}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []
    logo_path = _logo_path()

    # ── Header: logo + company block + accent rule ─────────────────────
    company_html = (
        f"<font name='{FONT_BOLD}' size=18 color='#2D1810'>"
        f"{settings.COMPANY_NAME}</font><br/>"
        f"<font name='{FONT_REGULAR}' size=8 color='#5C3D24'>"
        f"{settings.COMPANY_ADDRESS}</font>"
    )
    header_left = (
        Image(str(logo_path), width=1.6 * cm, height=1.6 * cm)
        if logo_path is not None
        else Paragraph("", s["small"])
    )
    header = Table(
        [[header_left, Paragraph(company_html, s["body"])]],
        colWidths=[2.0 * cm, 15.4 * cm],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(header)
    # Gold accent rule under the header.
    story.append(Spacer(1, 4))
    rule = Table([[""]], colWidths=[17.4 * cm], rowHeights=[2])
    rule.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_GOLD),
        ("LINEABOVE", (0, 0), (-1, -1), 0, BRAND_GOLD),
    ]))
    story.append(rule)
    story.append(Spacer(1, 10))

    # ── Title strip ────────────────────────────────────────────────────
    period_label = (
        f"{_MONTH_NAMES[payslip.month]} {payslip.year}"
        if 1 <= payslip.month <= 12
        else f"{payslip.month:02d}/{payslip.year}"
    )
    title_table = Table(
        [[
            Paragraph(
                f"<font name='{FONT_BOLD}' size=20 color='#2D1810'>"
                f"PAYSLIP</font>"
                f"<font name='{FONT_REGULAR}' size=12 color='#C8941A'>"
                f"  ·  {period_label}</font>",
                s["body"],
            ),
            Paragraph(
                f"Pay period <b>{payslip.month:02d}/{payslip.year}</b><br/>"
                f"Generated on {date.today().strftime('%d %b %Y')}",
                s["right"],
            ),
        ]],
        colWidths=[10.5 * cm, 6.9 * cm],
    )
    title_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 8))

    # ── Employee info (two columns) ────────────────────────────────────
    name = f"{employee.first_name} {employee.last_name}"
    desig = employee.designation.name if employee.designation else "—"
    dept = employee.department.name if employee.department else "—"

    left_pairs = [
        ("Name", name),
        ("Employee Code", employee.employee_code),
        ("Designation", desig),
        ("Department", dept),
    ]
    right_pairs = [
        ("UAN No.", employee.uan_number or "—"),
        ("PF No.", employee.pf_number or "—"),
        ("ESIC No.", employee.esic_number or "—"),
        (
            "Bank A/C",
            (
                f"{bank.bank_name} · {_mask_account(bank.account_no)}"
                if bank is not None
                else "Not on record"
            ),
        ),
    ]

    def _info_block(pairs: list[tuple[str, str]], *, label_w: float, value_w: float) -> Table:
        rows = []
        for k, v in pairs:
            rows.append([
                Paragraph(
                    f"<font name='{FONT_REGULAR}' size=8 color='#5C3D24'>"
                    f"{k.upper()}</font>",
                    s["body"],
                ),
                Paragraph(
                    f"<font name='{FONT_BOLD}' size=10 color='#2D1810'>"
                    f"{v}</font>",
                    s["body"],
                ),
            ])
        t = Table(rows, colWidths=[label_w, value_w])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, GRID),
        ]))
        return t

    info_card = Table(
        [[
            _info_block(left_pairs, label_w=2.7 * cm, value_w=5.5 * cm),
            _info_block(right_pairs, label_w=2.0 * cm, value_w=6.4 * cm),
        ]],
        colWidths=[8.5 * cm, 8.9 * cm],
    )
    info_card.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, GRID),
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_card)
    story.append(Spacer(1, 10))

    # ── Days paid / LOP strip ──────────────────────────────────────────
    def _fmt_days(v) -> str:
        from decimal import Decimal as _D
        d = _D(str(v or 0)).normalize()
        # ``.normalize()`` turns Decimal("30.00") into Decimal("3E+1") —
        # switch back to a plain integer when there's no fractional part
        # so the payslip reads "30", not "30.00" or "3E+1".
        if d == d.to_integral_value():
            return str(int(d))
        return format(d, "f").rstrip("0").rstrip(".")

    days_strip = Table(
        [[
            Paragraph(
                f"<font name='{FONT_REGULAR}' size=9 color='#5C3D24'>"
                f"DAYS PAID</font>  "
                f"<font name='{FONT_BOLD}' size=11 color='#2D1810'>"
                f"{_fmt_days(payslip.days_paid)} / "
                f"{_fmt_days(payslip.working_days)}</font>",
                s["body"],
            ),
            Paragraph(
                f"<font name='{FONT_REGULAR}' size=9 color='#5C3D24'>"
                f"DAYS LOP</font>  "
                f"<font name='{FONT_BOLD}' size=11 color='#2D1810'>"
                f"{_fmt_days(payslip.days_lop)}</font>",
                s["body"],
            ),
        ]],
        colWidths=[8.7 * cm, 8.7 * cm],
    )
    days_strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF6E9")),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(days_strip)
    story.append(Spacer(1, 10))

    # ── Salary breakup (monthly only) ──────────────────────────────────
    breakup_table = _salary_table(payslip.breakup or {}, show_annual=False)
    story.append(breakup_table)
    story.append(Spacer(1, 12))

    # ── Variable pay this month (approved incentives) ─────────────────
    incentive = Decimal(str(getattr(payslip, "incentive", 0) or 0))
    if incentive > 0:
        inc = Table(
            [[
                Paragraph(
                    f"<font name='{FONT_BOLD}'>Incentive (this month)</font><br/>"
                    "<font size=8>Included in gross pay; ESIC and professional tax apply.</font>",
                    s["body"],
                ),
                Paragraph(
                    f"<font name='{FONT_BOLD}'>{RUPEE} {int(incentive):,}</font>",
                    s["right"],
                ),
            ]],
            colWidths=[11.5 * cm, 5.5 * cm],
        )
        inc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF6E9")),
            ("BOX", (0, 0), (-1, -1), 0.5, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(inc)
        story.append(Spacer(1, 12))

    # ── Net pay banner ─────────────────────────────────────────────────
    net_row = Table(
        [[
            Paragraph(
                f"<font name='{FONT_BOLD}' size=12 color='#FFFFFF'>"
                f"NET PAY FOR {period_label.upper()}</font>",
                s["body"],
            ),
            Paragraph(
                f"<font name='{FONT_BOLD}' size=16 color='#FFFFFF'>"
                f"{RUPEE} {int(payslip.net_pay):,}</font>",
                s["right"],
            ),
        ]],
        colWidths=[10.4 * cm, 7.0 * cm],
    )
    net_row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_BROWN_DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(net_row)
    story.append(Spacer(1, 10))

    # ── Bank credit box (full account on record) ───────────────────────
    if bank is not None:
        bank_holder = (
            bank.account_holder_name
            or f"{employee.first_name} {employee.last_name}"
        )
        bank_html = (
            f"<font name='{FONT_REGULAR}' size=9 color='#5C3D24'>"
            f"SALARY CREDITED TO</font><br/>"
            f"<font name='{FONT_BOLD}' size=10 color='#2D1810'>"
            f"{bank_holder}</font>"
            f"<font name='{FONT_REGULAR}' size=9 color='#5C3D24'>"
            f"  ·  A/c {_mask_account(bank.account_no)}"
            f"  ·  {bank.bank_name}"
            f"{f'  ·  {bank.branch}' if bank.branch else ''}"
            f"  ·  IFSC {bank.ifsc}</font>"
        )
        bank_card = Table(
            [[Paragraph(bank_html, s["body"])]],
            colWidths=[17.4 * cm],
        )
        bank_card.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, GRID),
            ("BACKGROUND", (0, 0), (-1, -1), BRAND_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(bank_card)
        story.append(Spacer(1, 14))

    story.append(Paragraph(
        "This is a computer-generated payslip and does not require a signature.",
        s["small"],
    ))

    decorator = _make_payslip_page(logo_path)
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)
    return buffer.getvalue()

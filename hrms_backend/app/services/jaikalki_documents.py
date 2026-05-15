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
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Employee, GeneratedDocument, Payslip, User
from app.services.salary_calculator import JaikalkiSalaryCalculator
from app.services.storage import upload_fileobj


BRAND_BROWN = colors.HexColor("#3D2817")
BRAND_BROWN_DARK = colors.HexColor("#2D1810")
BRAND_GOLD = colors.HexColor("#C8941A")
BRAND_BG = colors.HexColor("#FDF8EE")
GRID = colors.HexColor("#E8DACA")


# ── Letter number sequencing ────────────────────────────────────────
async def _next_letter_number(
    db: AsyncSession, *, doc_type: str, year: int
) -> str:
    """Generate JKT/HR/AL/{seq}/{year} for offer letters or
    JKT/HR/CL/{seq}/{year} for confirmation letters."""
    code = "AL" if doc_type == "offer_letter" else "CL"
    rows = (
        await db.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.doc_type == doc_type)
            .where(GeneratedDocument.letter_number.is_not(None))
        )
    ).scalars().all()
    max_seq = 0
    for d in rows:
        if not d.letter_number:
            continue
        parts = d.letter_number.split("/")
        if len(parts) >= 5 and parts[-1] == str(year):
            try:
                max_seq = max(max_seq, int(parts[-2]))
            except ValueError:
                pass
    return f"JKT/HR/{code}/{(max_seq + 1):03d}/{year}"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s = {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, textColor=BRAND_BROWN_DARK,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=12, leading=15, spaceBefore=10, spaceAfter=4,
            textColor=BRAND_BROWN_DARK,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10, leading=14, alignment=4, textColor=BRAND_BROWN_DARK,
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9, leading=12, textColor=colors.dimgray,
        ),
        "right": ParagraphStyle(
            "right", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10, leading=13, alignment=2, textColor=BRAND_BROWN_DARK,
        ),
        "label": ParagraphStyle(
            "label", parent=base["BodyText"], fontName="Helvetica-Oblique",
            fontSize=9, leading=11, textColor=BRAND_GOLD,
        ),
        "company": ParagraphStyle(
            "company", parent=base["Title"], fontName="Helvetica-Bold",
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
    breakup = JaikalkiSalaryCalculator().calculate(
        employee.salary_template,
        ctc_annual=employee.ctc_annual or None,
        employee=employee,
    ).as_dict()

    pdf_bytes = _render_offer_letter(
        employee, letter_no=letter_no, on_date=letter_date, breakup=breakup
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
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"Offer Letter · {employee.employee_code}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    # ── Header ───────────────────────────────────────────────────────
    story.append(Paragraph(settings.COMPANY_NAME, s["company"]))
    story.append(
        Paragraph(settings.COMPANY_ADDRESS, s["small"])
    )
    story.append(Spacer(1, 14))

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
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
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
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
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
        ["Group Mediclaim", f"₹{int(employee.salary_template.mediclaim_amount or 0):,}"],
        [
            "Group Personal Accident",
            f"₹{int(employee.salary_template.pa_insurance_amount or 0):,}",
        ],
        ["Total Insurance", f"₹{int(insurance_total):,}"],
    ]
    ins = Table(insurance_rows, colWidths=[10 * cm, 7 * cm])
    ins.setStyle(_table_style(highlight_last=True))
    story.append(ins)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _salary_table(breakup: dict) -> Table:
    def fmt(n: int) -> str:
        return f"₹{int(n):,}"

    rows: list = [["Component", "Per Month (₹)", "Per Annum (₹)"]]

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
    rows.append(["EARNINGS", "", ""])
    for label, key in earnings_rows:
        v = int(breakup.get(key, 0) or 0)
        if v <= 0:
            continue
        rows.append([label, fmt(v), fmt(v * 12)])
    rows.append(
        ["Gross Salary", fmt(breakup["gross"]), fmt(breakup["gross"] * 12)]
    )

    rows.append(["EMPLOYEE DEDUCTIONS", "", ""])
    rows.append([
        "Provident Fund (Employee)",
        fmt(breakup["pf_employee"]),
        fmt(breakup["pf_employee"] * 12),
    ])
    rows.append([
        "ESIC (Employee)",
        fmt(breakup["esic_employee"]),
        fmt(breakup["esic_employee"] * 12),
    ])
    rows.append([
        "Professional Tax",
        fmt(breakup["professional_tax"]),
        fmt(breakup["professional_tax"] * 12),
    ])
    rows.append([
        "Total Deductions",
        fmt(breakup["total_deductions"]),
        fmt(breakup["total_deductions"] * 12),
    ])

    rows.append([
        "Net Salary",
        fmt(breakup["net_salary"]),
        fmt(breakup["net_salary"] * 12),
    ])

    rows.append(["EMPLOYER CONTRIBUTIONS", "", ""])
    rows.append([
        "Provident Fund (Employer)",
        fmt(breakup["pf_employer"]),
        fmt(breakup["pf_employer"] * 12),
    ])
    rows.append([
        "ESIC (Employer)",
        fmt(breakup["esic_employer"]),
        fmt(breakup["esic_employer"] * 12),
    ])

    rows.append([
        "TOTAL CTC",
        fmt(breakup["total_ctc_monthly"]),
        fmt(breakup["total_ctc_annual"]),
    ])

    t = Table(rows, colWidths=[8 * cm, 4.5 * cm, 4.5 * cm])

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
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
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
        style_cmds.append(("FONT", (0, i), (-1, i), "Helvetica-Bold", 9))
        style_cmds.append(("SPAN", (0, i), (-1, i)))
    for i in bold_idx:
        style_cmds.append(("FONT", (0, i), (-1, i), "Helvetica-Bold", 9))
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
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
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
        cmds.append(("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 10))
        cmds.append(
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FBF6E9"))
        )
    return TableStyle(cmds)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
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
                f"<b>₹{breakup['total_ctc_annual']:,} per annum</b> "
                f"(₹{breakup['total_ctc_monthly']:,} per month). The detailed "
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

    pdf_bytes = _render_confirmation_letter(
        employee, letter_no=letter_no, on_date=letter_date
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
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"Confirmation Letter · {employee.employee_code}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    story.append(Paragraph(settings.COMPANY_NAME, s["company"]))
    story.append(Paragraph(settings.COMPANY_ADDRESS, s["small"]))
    story.append(Spacer(1, 14))

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
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


# ── Payslip PDF ───────────────────────────────────────────────────────
def render_payslip_pdf(
    payslip: Payslip,
    employee: Employee,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"Payslip · {employee.employee_code} · "
              f"{payslip.month:02d}/{payslip.year}",
        author=settings.COMPANY_NAME,
    )
    s = _styles()
    story: list = []

    story.append(Paragraph(settings.COMPANY_NAME, s["company"]))
    story.append(Paragraph(settings.COMPANY_ADDRESS, s["small"]))
    story.append(Spacer(1, 12))

    title_row = Table(
        [[
            Paragraph(
                f"<b>Payslip · {payslip.month:02d}/{payslip.year}</b>",
                s["title"],
            ),
            Paragraph(
                f"Generated on {date.today().strftime('%d %b %Y')}",
                s["right"],
            ),
        ]],
        colWidths=[10 * cm, 7 * cm],
    )
    title_row.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(title_row)
    story.append(Spacer(1, 6))

    info_rows = [
        ["Name", f"{employee.first_name} {employee.last_name}"],
        [
            "Designation",
            employee.designation.name if employee.designation else "—",
        ],
        ["Employee Code", employee.employee_code],
        [
            "Department",
            employee.department.name if employee.department else "—",
        ],
        ["Days Paid", f"{payslip.days_paid} / {payslip.working_days}"],
        ["Days LOP", f"{payslip.days_lop}"],
    ]
    info = Table(info_rows, colWidths=[5 * cm, 12 * cm])
    info.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN_DARK),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, GRID),
        ("BACKGROUND", (0, 0), (0, -1), BRAND_BG),
    ]))
    story.append(info)
    story.append(Spacer(1, 12))

    breakup_table = _salary_table(payslip.breakup or {})
    story.append(breakup_table)
    story.append(Spacer(1, 12))

    net_row = Table(
        [["Net pay this month", f"₹{int(payslip.net_pay):,}"]],
        colWidths=[10 * cm, 7 * cm],
    )
    net_row.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica-Bold", 12),
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_GOLD),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(net_row)

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "This is a computer-generated payslip and does not require a signature.",
        s["small"],
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()

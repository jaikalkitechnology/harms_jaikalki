"""Increment-letter PDF — brown + gold Jaikalki branding."""
from __future__ import annotations

import io
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import Designation, Employee, SalaryRevision

BRAND_BROWN = colors.HexColor("#3D2817")
BRAND_GOLD = colors.HexColor("#F4B71F")
BRAND_GOLD_DARK = colors.HexColor("#C8941A")
BRAND_CREAM = colors.HexColor("#FBF6E9")


def render_increment_letter(
    *,
    revision: SalaryRevision,
    employee: Employee,
    designation: Optional[Designation] = None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Increment letter {employee.employee_code}",
    )
    styles = getSampleStyleSheet()
    h_brand = ParagraphStyle(
        "h_brand",
        parent=styles["Heading1"],
        textColor=BRAND_BROWN,
        fontSize=20,
        spaceAfter=4,
    )
    h_section = ParagraphStyle(
        "h_section",
        parent=styles["Heading2"],
        textColor=BRAND_GOLD_DARK,
        fontSize=14,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        textColor=BRAND_BROWN,
        fontSize=10.5,
        leading=15,
    )
    small = ParagraphStyle(
        "small",
        parent=body,
        fontSize=8,
        textColor=colors.grey,
    )

    full_name = f"{employee.first_name} {employee.last_name}".strip()
    designation_name = designation.name if designation else "—"
    new_ctc = int(revision.new_ctc_annual)
    prev_ctc = int(revision.previous_ctc_annual)

    story = []
    story.append(Paragraph("JAIKALKI TECHNOLOGY PVT LTD", h_brand))
    story.append(
        Paragraph(
            "Compensation revision · Confidential",
            ParagraphStyle("sub", parent=body, textColor=BRAND_GOLD_DARK),
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("LETTER OF SALARY REVISION", h_section))

    meta_data = [
        ["Employee", full_name, "Code", employee.employee_code],
        [
            "Designation",
            designation_name,
            "Effective from",
            revision.effective_date.strftime("%d %B %Y"),
        ],
        [
            "Reason",
            revision.reason.replace("_", " ").title(),
            "Date issued",
            revision.applied_at.strftime("%d %B %Y")
            if revision.applied_at
            else "—",
        ],
    ]
    meta = Table(meta_data, colWidths=[2.4 * cm, 6.6 * cm, 2.6 * cm, 5 * cm])
    meta.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph(f"Dear {full_name},", body))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "We are pleased to inform you that, in recognition of your "
            "contribution to Jaikalki Technology Pvt Ltd, your annual "
            f"cost-to-company has been revised with effect from "
            f"<b>{revision.effective_date.strftime('%d %B %Y')}</b>.",
            body,
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    rev_data = [
        ["", "Previous", "Revised", "Increment"],
        [
            "Annual CTC (₹)",
            f"{prev_ctc:,}",
            f"{new_ctc:,}",
            f"+{new_ctc - prev_ctc:,}  ({revision.increment_pct}%)",
        ],
    ]
    rev = Table(rev_data, colWidths=[5 * cm, 4 * cm, 4 * cm, 4.6 * cm])
    rev.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BROWN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BACKGROUND", (3, 1), (3, 1), BRAND_GOLD),
                ("FONTNAME", (3, 1), (3, 1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E8DACA")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(rev)
    story.append(Spacer(1, 0.5 * cm))

    # Monthly breakup table if available
    if revision.breakup_snapshot:
        monthly = revision.breakup_snapshot.get("monthly", {})
        if monthly:
            story.append(Paragraph("Revised monthly salary breakup", h_section))
            rows = [["Component", "Amount (₹)"]]
            for label, key in [
                ("Basic", "basic"),
                ("HRA", "hra"),
                ("Other allowance", "other_allowance"),
                ("Conveyance", "conveyance"),
                ("Gross", "gross"),
                ("PF (employee)", "pf_employee"),
                ("ESIC (employee)", "esic_employee"),
                ("Professional tax", "professional_tax"),
                ("Net pay", "net"),
            ]:
                if key in monthly:
                    rows.append([label, f"{int(monthly[key]):,}"])
            br = Table(rows, colWidths=[10 * cm, 6.6 * cm])
            br.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GOLD_DARK),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, BRAND_CREAM],
                        ),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E8DACA")),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(br)
            story.append(Spacer(1, 0.4 * cm))

    if revision.notes:
        story.append(Paragraph("Notes", h_section))
        story.append(Paragraph(revision.notes, body))
        story.append(Spacer(1, 0.4 * cm))

    story.append(
        Paragraph(
            "All other terms and conditions of your employment remain "
            "unchanged. Please retain this letter for your records.",
            body,
        )
    )
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Wishing you continued success,", body))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("<b>Human Resources</b>", body))
    story.append(Paragraph("Jaikalki Technology Pvt Ltd", body))

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            "This letter is system-generated and digitally signed by the "
            "Jaikalki HRMS. It does not require a physical signature.",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()

"""Certificate PDF renderer with QR verification code."""
from __future__ import annotations

import io
from typing import Optional

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.models import Certificate, Employee


BRAND_BROWN = colors.HexColor("#3D2817")
BRAND_GOLD = colors.HexColor("#F4B71F")
BRAND_GOLD_DARK = colors.HexColor("#C8941A")
BRAND_CREAM = colors.HexColor("#FBF6E9")


def _generate_qr_image(verify_url: str) -> Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#3D2817", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=3 * cm, height=3 * cm)


def render_certificate(
    *,
    certificate: Certificate,
    employee: Employee,
    verify_base_url: Optional[str] = None,
) -> bytes:
    base = verify_base_url or "https://portal.jaikalki.com"
    verify_url = (
        f"{base}/lms/certificates/verify/{certificate.certificate_number}"
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Certificate {certificate.certificate_number}",
    )
    styles = getSampleStyleSheet()
    h_brand = ParagraphStyle(
        "h_brand",
        parent=styles["Heading1"],
        textColor=BRAND_BROWN,
        fontSize=24,
        alignment=1,
        spaceAfter=4,
    )
    sub_brand = ParagraphStyle(
        "sub_brand",
        parent=styles["BodyText"],
        textColor=BRAND_GOLD_DARK,
        fontSize=12,
        alignment=1,
    )
    cert_title = ParagraphStyle(
        "cert_title",
        parent=styles["Heading2"],
        textColor=BRAND_GOLD_DARK,
        fontSize=28,
        alignment=1,
        spaceBefore=18,
        spaceAfter=18,
    )
    awarded_to = ParagraphStyle(
        "awarded",
        parent=styles["BodyText"],
        textColor=BRAND_BROWN,
        fontSize=14,
        alignment=1,
    )
    name_style = ParagraphStyle(
        "name",
        parent=styles["Heading2"],
        textColor=BRAND_BROWN,
        fontSize=26,
        alignment=1,
        spaceAfter=12,
    )
    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        textColor=BRAND_BROWN,
        fontSize=12,
        alignment=1,
        leading=18,
    )
    small = ParagraphStyle(
        "small",
        parent=styles["BodyText"],
        textColor=colors.grey,
        fontSize=8,
        alignment=1,
    )

    story = []
    story.append(Paragraph("JAIKALKI TECHNOLOGY PVT LTD", h_brand))
    story.append(
        Paragraph(
            "Learning &amp; Certification · Established to empower people",
            sub_brand,
        )
    )
    story.append(Paragraph("CERTIFICATE OF ACHIEVEMENT", cert_title))

    story.append(Paragraph("This certifies that", awarded_to))
    full_name = f"{employee.first_name} {employee.last_name}".strip()
    story.append(Paragraph(f"<b>{full_name}</b>", name_style))
    story.append(
        Paragraph(
            f"Employee Code <b>{employee.employee_code}</b>",
            ParagraphStyle("emp", parent=body, fontSize=10),
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    score = (
        f" with a score of <b>{certificate.score_percentage}%</b>"
        if certificate.score_percentage is not None
        else ""
    )
    story.append(
        Paragraph(
            f"has successfully completed <b>{certificate.title}</b>{score}.",
            body,
        )
    )

    story.append(Spacer(1, 0.6 * cm))

    # Footer band: certificate number + dates + QR
    footer_data = [
        [
            Paragraph(
                f"<b>Certificate No.</b><br/>{certificate.certificate_number}",
                ParagraphStyle("cn", parent=body, fontSize=10, alignment=0),
            ),
            Paragraph(
                f"<b>Issued</b><br/>{certificate.issued_date.strftime('%d %B %Y')}",
                ParagraphStyle("d1", parent=body, fontSize=10, alignment=1),
            ),
            Paragraph(
                f"<b>Valid until</b><br/>"
                f"{certificate.expiry_date.strftime('%d %B %Y') if certificate.expiry_date else 'No expiry'}",
                ParagraphStyle("d2", parent=body, fontSize=10, alignment=1),
            ),
            _generate_qr_image(verify_url),
        ]
    ]
    footer = Table(
        footer_data,
        colWidths=[7 * cm, 5 * cm, 5 * cm, 4 * cm],
    )
    footer.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), BRAND_CREAM),
                ("BOX", (0, 0), (-1, -1), 1, BRAND_BROWN),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(footer)
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            f"Verify this certificate at {verify_url}",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()

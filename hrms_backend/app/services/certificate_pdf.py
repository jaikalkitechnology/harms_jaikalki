"""Certificate PDF renderer — elegant landscape layout with gold border,
watermark, signature line, and QR verification code."""
from __future__ import annotations

import io
from typing import Optional

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen.canvas import Canvas
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
BRAND_BROWN_DARK = colors.HexColor("#2D1810")
BRAND_GOLD = colors.HexColor("#F4B71F")
BRAND_GOLD_DARK = colors.HexColor("#C8941A")
BRAND_GOLD_LIGHT = colors.HexColor("#FFE08A")
BRAND_CREAM = colors.HexColor("#FDF8EE")
INK_GREY = colors.HexColor("#5C3D24")


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
    return Image(buf, width=2.6 * cm, height=2.6 * cm)


def _draw_decorations(canvas: Canvas, doc) -> None:
    """Page decorations drawn underneath the flowables: cream wash, double
    gold border, corner ornaments, and a soft brand watermark."""
    width, height = landscape(A4)

    # Cream background fill
    canvas.saveState()
    canvas.setFillColor(BRAND_CREAM)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    # Outer thin gold rule
    canvas.setStrokeColor(BRAND_GOLD_DARK)
    canvas.setLineWidth(1)
    canvas.rect(10 * mm, 10 * mm, width - 20 * mm, height - 20 * mm, stroke=1, fill=0)

    # Inner thicker gold rule
    canvas.setStrokeColor(BRAND_GOLD)
    canvas.setLineWidth(3)
    canvas.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm, stroke=1, fill=0)

    # Innermost hairline brown border
    canvas.setStrokeColor(BRAND_BROWN)
    canvas.setLineWidth(0.4)
    canvas.rect(18 * mm, 18 * mm, width - 36 * mm, height - 36 * mm, stroke=1, fill=0)

    # Corner ornaments — small diamonds
    for cx, cy in (
        (18 * mm, 18 * mm),
        (width - 18 * mm, 18 * mm),
        (18 * mm, height - 18 * mm),
        (width - 18 * mm, height - 18 * mm),
    ):
        canvas.setFillColor(BRAND_GOLD_DARK)
        canvas.setStrokeColor(BRAND_BROWN)
        canvas.setLineWidth(0.5)
        path = canvas.beginPath()
        path.moveTo(cx, cy + 4 * mm)
        path.lineTo(cx + 4 * mm, cy)
        path.lineTo(cx, cy - 4 * mm)
        path.lineTo(cx - 4 * mm, cy)
        path.close()
        canvas.drawPath(path, stroke=1, fill=1)

    # Faint watermark "JAIKALKI" rotated
    canvas.saveState()
    canvas.translate(width / 2, height / 2)
    canvas.rotate(20)
    canvas.setFillColor(colors.Color(0.78, 0.66, 0.42, alpha=0.08))
    canvas.setFont("Helvetica-Bold", 90)
    canvas.drawCentredString(0, -25, "JAIKALKI")
    canvas.restoreState()

    # Top ribbon — gold band with small medal
    ribbon_y = height - 26 * mm
    canvas.setFillColor(BRAND_GOLD)
    canvas.rect(width / 2 - 30 * mm, ribbon_y, 60 * mm, 6 * mm, stroke=0, fill=1)
    # Medal circle
    canvas.setFillColor(BRAND_GOLD_DARK)
    canvas.circle(width / 2, ribbon_y + 3 * mm, 6 * mm, stroke=0, fill=1)
    canvas.setFillColor(BRAND_CREAM)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(width / 2, ribbon_y + 1.4 * mm, "JKT")

    canvas.restoreState()


# Map certificate_type -> display heading
_CERT_HEADINGS = {
    "achievement": ("Certificate of Achievement",
                    "presented in recognition of dedication, learning, and excellence"),
    "appreciation": ("Certificate of Appreciation",
                     "with sincere gratitude for outstanding contribution and support"),
    "completion": ("Certificate of Completion",
                   "in acknowledgement of the successful completion of the programme"),
    "participation": ("Certificate of Participation",
                      "for active participation and engagement"),
    "excellence": ("Certificate of Excellence",
                   "presented for exemplary performance and standards of excellence"),
    "training": ("Training Completion Certificate",
                 "in recognition of the successful completion of the training programme"),
}


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

    cert_type = (getattr(certificate, "certificate_type", None) or "achievement").lower()
    if cert_type == "custom":
        heading_text = certificate.title
        sub_text = ""
    else:
        heading_text, sub_text = _CERT_HEADINGS.get(
            cert_type, _CERT_HEADINGS["achievement"]
        )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=3.2 * cm,
        rightMargin=3.2 * cm,
        topMargin=3.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"Certificate {certificate.certificate_number}",
        author="Jaikalki Technology Pvt Ltd",
    )
    styles = getSampleStyleSheet()

    h_brand = ParagraphStyle(
        "h_brand",
        parent=styles["Heading1"],
        textColor=BRAND_BROWN_DARK,
        fontSize=22,
        leading=26,
        alignment=1,
        spaceAfter=2,
    )
    sub_brand = ParagraphStyle(
        "sub_brand",
        parent=styles["BodyText"],
        textColor=BRAND_GOLD_DARK,
        fontSize=10,
        alignment=1,
        spaceAfter=10,
    )
    cert_title = ParagraphStyle(
        "cert_title",
        parent=styles["Heading2"],
        textColor=BRAND_GOLD_DARK,
        fontSize=30,
        leading=36,
        alignment=1,
        spaceBefore=12,
        spaceAfter=4,
    )
    cert_subtitle = ParagraphStyle(
        "cert_subtitle",
        parent=styles["BodyText"],
        textColor=INK_GREY,
        fontSize=11,
        alignment=1,
        spaceAfter=20,
    )
    awarded_to = ParagraphStyle(
        "awarded",
        parent=styles["BodyText"],
        textColor=INK_GREY,
        fontSize=14,
        alignment=1,
        spaceAfter=6,
    )
    name_style = ParagraphStyle(
        "name",
        parent=styles["Heading2"],
        textColor=BRAND_BROWN_DARK,
        fontSize=32,
        leading=38,
        alignment=1,
        spaceAfter=4,
    )
    emp_code_style = ParagraphStyle(
        "empc",
        parent=styles["BodyText"],
        textColor=INK_GREY,
        fontSize=10,
        alignment=1,
        spaceAfter=14,
    )
    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        textColor=BRAND_BROWN,
        fontSize=13,
        alignment=1,
        leading=20,
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
            "Learning &amp; Certification · est. to empower people",
            sub_brand,
        )
    )
    story.append(Paragraph(heading_text, cert_title))
    if sub_text:
        story.append(Paragraph(sub_text, cert_subtitle))
    else:
        story.append(Spacer(1, 0.2 * cm))

    awarded_label = {
        "appreciation": "Presented to",
        "participation": "Awarded to",
        "completion": "This is to certify that",
        "excellence": "Awarded to",
        "training": "This is to certify that",
        "custom": "Awarded to",
    }.get(cert_type, "This is to certify that")
    story.append(Paragraph(awarded_label, awarded_to))

    full_name = f"{employee.first_name} {employee.last_name}".strip()
    story.append(Paragraph(f"<b>{full_name}</b>", name_style))
    story.append(
        Paragraph(
            f"Employee Code &nbsp;<b>{employee.employee_code}</b>",
            emp_code_style,
        )
    )

    body_text = (getattr(certificate, "body_text", None) or "").strip()
    if body_text:
        # Admin-supplied custom body — render verbatim (with line breaks).
        story.append(
            Paragraph(body_text.replace("\n", "<br/>"), body)
        )
    else:
        score = (
            f" with a score of <b>{certificate.score_percentage}%</b>"
            if certificate.score_percentage is not None
            else ""
        )
        verb = {
            "appreciation": "in heartfelt appreciation for",
            "participation": "for participating in",
            "completion": "for successfully completing",
            "excellence": "in recognition of excellence in",
            "training": "for successfully completing the training",
            "custom": "for",
        }.get(cert_type, "has successfully completed")
        story.append(
            Paragraph(
                f"{verb} <b>{certificate.title}</b>{score}.",
                body,
            )
        )

    story.append(Spacer(1, 0.8 * cm))

    # Signature row + QR
    sig_line = Paragraph(
        '<para align="center">'
        '<font color="#3D2817">_________________________</font><br/>'
        '<font size="9" color="#5C3D24">Authorized Signatory</font>'
        '</para>',
        body,
    )
    seal = Paragraph(
        '<para align="center">'
        '<font size="9" color="#5C3D24">Issued by</font><br/>'
        '<font color="#C8941A" size="11"><b>Jaikalki HR &amp; Learning</b></font>'
        '</para>',
        body,
    )
    qr_img = _generate_qr_image(verify_url)
    sig_row = Table(
        [[sig_line, seal, qr_img]],
        colWidths=[8 * cm, 8 * cm, 4 * cm],
    )
    sig_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(sig_row)

    story.append(Spacer(1, 0.5 * cm))

    # Footer band: certificate number + dates
    footer_data = [
        [
            Paragraph(
                f"<b>Certificate No.</b><br/>{certificate.certificate_number}",
                ParagraphStyle("cn", parent=body, fontSize=10, alignment=1),
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
        ]
    ]
    footer = Table(footer_data, colWidths=[7 * cm, 6 * cm, 6 * cm])
    footer.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(1, 1, 1, alpha=0.6)),
                ("BOX", (0, 0), (-1, -1), 0.5, BRAND_GOLD_DARK),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(footer)
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            f"Scan the QR code or visit {verify_url} to verify this certificate.",
            small,
        )
    )

    if certificate.is_revoked:
        story.append(Spacer(1, 0.3 * cm))
        story.append(
            Paragraph(
                "<b><font color='#C53030'>REVOKED — this certificate is no longer valid.</font></b>",
                small,
            )
        )

    doc.build(
        story, onFirstPage=_draw_decorations, onLaterPages=_draw_decorations
    )
    return buf.getvalue()

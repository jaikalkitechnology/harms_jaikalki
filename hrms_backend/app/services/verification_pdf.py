"""Verification report PDF renderer."""
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

from app.models import Employee, Verification, VerificationTemplate

BRAND_BROWN = colors.HexColor("#3D2817")
BRAND_GOLD = colors.HexColor("#F4B71F")
BRAND_GOLD_DARK = colors.HexColor("#C8941A")


_RESULT_COLOR = {
    "positive": colors.HexColor("#5E8B3A"),
    "negative": colors.HexColor("#C53030"),
    "unable_to_verify": colors.HexColor("#E89F1A"),
    "partial": colors.HexColor("#2C7A7B"),
}


def render_verification_report(
    *,
    verification: Verification,
    template: VerificationTemplate,
    verifier: Optional[Employee],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Verification Report {verification.ticket_number}",
    )
    styles = getSampleStyleSheet()
    h_brand = ParagraphStyle(
        "h_brand",
        parent=styles["Heading1"],
        textColor=BRAND_BROWN,
        fontSize=18,
        spaceAfter=4,
    )
    h_section = ParagraphStyle(
        "h_section",
        parent=styles["Heading3"],
        textColor=BRAND_GOLD_DARK,
        fontSize=11,
        spaceAfter=4,
        spaceBefore=12,
    )
    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        textColor=BRAND_BROWN,
        fontSize=10,
        leading=14,
    )

    story = []
    story.append(Paragraph("JAIKALKI TECHNOLOGY PVT LTD", h_brand))
    story.append(
        Paragraph(
            "Background Verification · Confidential Report",
            ParagraphStyle("sub", parent=body, textColor=BRAND_GOLD_DARK),
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # Header band
    header_data = [
        ["Ticket", verification.ticket_number, "Type", verification.type.upper()],
        [
            "Subject",
            verification.subject_name,
            "Result",
            (verification.result or "PENDING").upper().replace("_", " "),
        ],
        [
            "Assigned",
            verification.assigned_at.strftime("%d-%b-%Y %H:%M"),
            "Submitted",
            verification.submitted_at.strftime("%d-%b-%Y %H:%M")
            if verification.submitted_at
            else "—",
        ],
        [
            "Deadline",
            verification.deadline_at.strftime("%d-%b-%Y %H:%M")
            if verification.deadline_at
            else "—",
            "Verifier",
            f"{verifier.first_name} {verifier.last_name} ({verifier.employee_code})"
            if verifier
            else "—",
        ],
    ]
    header = Table(header_data, colWidths=[2 * cm, 6.5 * cm, 2.2 * cm, 6 * cm])
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF6E9")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN),
                (
                    "TEXTCOLOR",
                    (3, 1),
                    (3, 1),
                    _RESULT_COLOR.get(verification.result or "", BRAND_BROWN),
                ),
                (
                    "FONTNAME",
                    (3, 1),
                    (3, 1),
                    "Helvetica-Bold",
                ),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.5, BRAND_BROWN),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E8DACA")),
            ]
        )
    )
    story.append(header)

    # Subject details
    story.append(Paragraph("★ SUBJECT DETAILS", h_section))
    if verification.address:
        story.append(Paragraph(f"<b>Address:</b> {verification.address}", body))
    if verification.contact_phone:
        story.append(Paragraph(f"<b>Phone:</b> {verification.contact_phone}", body))
    if verification.requested_by_org:
        story.append(
            Paragraph(
                f"<b>Requested by:</b> {verification.requested_by_org}", body
            )
        )
    for key, value in (verification.subject_data or {}).items():
        story.append(Paragraph(f"<b>{key}:</b> {value}", body))

    # Form findings
    if verification.form_data:
        story.append(Paragraph("★ VERIFICATION FINDINGS", h_section))
        rows = [["Field", "Finding"]]
        field_specs = {f["key"]: f for f in (template.fields or [])}
        for key, value in verification.form_data.items():
            label = field_specs.get(key, {}).get("label", key)
            rows.append([label, str(value)])
        findings = Table(rows, colWidths=[5 * cm, 11.7 * cm])
        findings.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND_BROWN),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#FBF6E9")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E8DACA")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(findings)

    # Remarks
    if verification.remarks:
        story.append(Paragraph("★ REMARKS", h_section))
        story.append(Paragraph(verification.remarks, body))

    # Audit info
    if verification.audited_at:
        story.append(Paragraph("★ AUDIT", h_section))
        story.append(
            Paragraph(
                f"<b>Status:</b> {verification.audit_status} · "
                f"<b>On:</b> {verification.audited_at.strftime('%d-%b-%Y %H:%M')}",
                body,
            )
        )
        if verification.audit_comments:
            story.append(
                Paragraph(f"<b>Comments:</b> {verification.audit_comments}", body)
            )

    # Fraud flags
    if verification.fraud_flags:
        story.append(Paragraph("★ FRAUD FLAGS", h_section))
        for flag in verification.fraud_flags:
            story.append(
                Paragraph(
                    f"• <b>{flag.flag_type}</b> ({flag.severity}, "
                    f"{flag.detected_by}) — {flag.notes or '—'}",
                    body,
                )
            )

    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            "<i>This report is system-generated by the Jaikalki HRMS. "
            "Findings are for the requesting organization only and may not be "
            "redistributed without written consent.</i>",
            ParagraphStyle("note", parent=body, fontSize=8, textColor=colors.grey),
        )
    )

    doc.build(story)
    return buf.getvalue()

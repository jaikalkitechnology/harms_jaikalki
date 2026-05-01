"""Quote PDF renderer with Jaikalki branding."""
from __future__ import annotations

import io
from decimal import Decimal

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

from app.models import Customer, Employee, Quote


BRAND_BROWN = colors.HexColor("#3D2817")
BRAND_GOLD = colors.HexColor("#F4B71F")
BRAND_GOLD_DARK = colors.HexColor("#C8941A")


def render_quote_pdf(
    *, quote: Quote, customer: Customer, employee: Employee
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Quotation {quote.quote_number}",
    )
    styles = getSampleStyleSheet()
    h_brand = ParagraphStyle(
        "h_brand",
        parent=styles["Heading1"],
        textColor=BRAND_BROWN,
        fontSize=20,
        spaceAfter=4,
    )
    h_quote = ParagraphStyle(
        "h_quote",
        parent=styles["Heading2"],
        textColor=BRAND_GOLD_DARK,
        fontSize=14,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        textColor=BRAND_BROWN,
        fontSize=10,
        leading=14,
    )
    small = ParagraphStyle(
        "small", parent=body, fontSize=8, textColor=colors.grey
    )

    story = []
    story.append(Paragraph("JAIKALKI TECHNOLOGY PVT LTD", h_brand))
    story.append(
        Paragraph(
            "Field Sales · Service · Solutions",
            ParagraphStyle("sub", parent=body, textColor=BRAND_GOLD_DARK),
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"QUOTATION · {quote.quote_number}", h_quote))
    story.append(Spacer(1, 0.2 * cm))

    # Bill-to + meta
    meta_data = [
        ["Bill to:", customer.name, "Quote No.", quote.quote_number],
        [
            "",
            customer.address or "-",
            "Date",
            quote.created_at.strftime("%d-%b-%Y"),
        ],
        [
            "",
            f"{customer.city or ''} {customer.pincode or ''}",
            "Valid until",
            quote.valid_until.strftime("%d-%b-%Y") if quote.valid_until else "-",
        ],
        [
            "",
            customer.gst or "",
            "Prepared by",
            f"{employee.first_name} {employee.last_name}",
        ],
    ]
    meta = Table(meta_data, colWidths=[2.2 * cm, 7 * cm, 2.6 * cm, 5 * cm])
    meta.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 0.5 * cm))

    # Line-item table
    rows = [["#", "Item", "Qty", "Unit price", "Tax %", "Amount"]]
    for i, li in enumerate(quote.line_items, start=1):
        unit_price = Decimal(str(li["unit_price"]))
        qty = int(li["quantity"])
        line_total = unit_price * qty
        rows.append(
            [
                str(i),
                li.get("name", "-"),
                str(qty),
                f"₹{unit_price:,.2f}",
                f"{li.get('tax_pct', '18')}%",
                f"₹{line_total:,.2f}",
            ]
        )
    items_table = Table(
        rows,
        colWidths=[0.8 * cm, 8 * cm, 1.5 * cm, 2.5 * cm, 1.6 * cm, 2.4 * cm],
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BROWN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF6E9")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E8DACA")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 0.4 * cm))

    # Totals
    totals_data = [
        ["Subtotal", f"₹{quote.subtotal:,.2f}"],
        [
            f"Discount ({quote.discount_pct}%)",
            f"– ₹{quote.discount_amount:,.2f}",
        ],
        ["Tax", f"₹{quote.tax_amount:,.2f}"],
        ["TOTAL", f"₹{quote.total_amount:,.2f}"],
    ]
    totals = Table(totals_data, colWidths=[12 * cm, 4.8 * cm])
    totals.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_BROWN),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), BRAND_GOLD),
                ("TEXTCOLOR", (0, -1), (-1, -1), BRAND_BROWN),
                ("LINEABOVE", (0, -1), (-1, -1), 1, BRAND_BROWN),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(totals)

    if quote.notes:
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph("<b>Notes:</b>", body))
        story.append(Paragraph(quote.notes, body))

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            "This quotation is system-generated by the Jaikalki HRMS. "
            "All prices are in Indian Rupees and inclusive of applicable taxes "
            "as shown above.",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()

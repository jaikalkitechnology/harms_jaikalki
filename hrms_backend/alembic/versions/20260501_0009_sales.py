"""Sales field force: leads, opportunities, products, quotes, orders, targets, promotions

Revision ID: 20260501_0009
Revises: 20260501_0008
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0009"
down_revision: Union[str, None] = "20260501_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLE_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    # ── Leads ────────────────────────────────────────────────────────
    op.create_table(
        "sales_leads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contact_name", sa.String(120), nullable=True),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("contact_email", sa.String(160), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "website", "referral", "cold_call", "exhibition", "campaign",
                "field_visit", "partner", "other",
                name="lead_source",
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column(
            "stage",
            sa.Enum(
                "new", "contacted", "qualified", "proposal", "negotiation",
                "won", "lost",
                name="lead_stage",
            ),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "expected_value",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column(
            "assigned_to",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_action", sa.String(255), nullable=True),
        sa.Column("next_action_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("lost_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_sales_leads_customer_id", "sales_leads", ["customer_id"])
    op.create_index("ix_sales_leads_stage", "sales_leads", ["stage"])
    op.create_index("ix_sales_leads_assigned_to", "sales_leads", ["assigned_to"])

    # ── Opportunities ────────────────────────────────────────────────
    op.create_table(
        "sales_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "lead_id",
            sa.Integer(),
            sa.ForeignKey("sales_leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "stage",
            sa.Enum(
                "discovery", "demo", "proposal", "negotiation", "closed_won",
                "closed_lost",
                name="opportunity_stage",
            ),
            nullable=False,
            server_default="discovery",
        ),
        sa.Column("probability", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("products", sa.JSON(), nullable=True),
        sa.Column("competitor", sa.String(160), nullable=True),
        sa.Column("next_action", sa.String(255), nullable=True),
        sa.Column("next_action_date", sa.Date(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_sales_opportunities_lead_id", "sales_opportunities", ["lead_id"]
    )

    # ── Products ─────────────────────────────────────────────────────
    op.create_table(
        "sales_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sku", sa.String(48), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(96), nullable=True),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "tax_pct", sa.Numeric(5, 2), nullable=False, server_default="18.00"
        ),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("brochure_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("sku", name="uq_product_sku"),
        **_TABLE_KW,
    )
    op.create_index("ix_sales_products_sku", "sales_products", ["sku"])

    # ── Quotes ───────────────────────────────────────────────────────
    op.create_table(
        "sales_quotes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("quote_number", sa.String(48), nullable=False),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            sa.Integer(),
            sa.ForeignKey("sales_leads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("line_items", sa.JSON(), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "sent", "accepted", "rejected", "expired",
                name="quote_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("signature_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("quote_number", name="uq_quote_number"),
        **_TABLE_KW,
    )
    op.create_index("ix_sales_quotes_customer_id", "sales_quotes", ["customer_id"])
    op.create_index("ix_sales_quotes_employee_id", "sales_quotes", ["employee_id"])

    # ── Orders ───────────────────────────────────────────────────────
    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_number", sa.String(48), nullable=False),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "quote_id",
            sa.Integer(),
            sa.ForeignKey("sales_quotes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("line_items", sa.JSON(), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_terms", sa.String(96), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "confirmed", "processing", "shipped", "delivered",
                "cancelled",
                name="order_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("tracking_number", sa.String(96), nullable=True),
        sa.Column("placed_at", sa.DateTime(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("order_number", name="uq_order_number"),
        **_TABLE_KW,
    )
    op.create_index("ix_sales_orders_customer_id", "sales_orders", ["customer_id"])
    op.create_index("ix_sales_orders_employee_id", "sales_orders", ["employee_id"])
    op.create_index("ix_sales_orders_status", "sales_orders", ["status"])

    # ── Targets ──────────────────────────────────────────────────────
    op.create_table(
        "sales_targets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "period_type",
            sa.Enum("monthly", "quarterly", "yearly", name="target_period_type"),
            nullable=False,
            server_default="monthly",
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "achieved_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "commission_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="2.00",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index("ix_sales_targets_employee_id", "sales_targets", ["employee_id"])

    # ── Promotion activities ─────────────────────────────────────────
    op.create_table(
        "sales_promotions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_name", sa.String(160), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("banners_placed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "brochures_distributed",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("demos_given", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "leads_collected", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **_TABLE_KW,
    )
    op.create_index(
        "ix_sales_promotions_employee_id", "sales_promotions", ["employee_id"]
    )
    op.create_index(
        "ix_sales_promotions_activity_date", "sales_promotions", ["activity_date"]
    )


def downgrade() -> None:
    op.drop_table("sales_promotions")
    op.drop_table("sales_targets")
    op.drop_table("sales_orders")
    op.drop_table("sales_quotes")
    op.drop_table("sales_products")
    op.drop_table("sales_opportunities")
    op.drop_table("sales_leads")

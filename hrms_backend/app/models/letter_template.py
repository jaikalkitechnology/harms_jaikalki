"""Letter / document templates for the HR generator.

Each template stores a placeholder-bearing body (``{{first_name}}``,
``{{employee_code}}`` etc.). The Letters admin page edits these; the
employee detail page renders any active template into a PDF stamped
with the Jaikalki letterhead.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args


class LetterTemplate(Base, TimestampMixin):
    __tablename__ = "letter_templates"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(
            "offer",
            "appointment",
            "confirmation",
            "experience",
            "increment",
            "termination",
            "warning",
            "policy",
            "other",
            name="letter_template_category",
        ),
        default="other",
        nullable=False,
    )
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Comma-separated list of supported placeholder keys, for the UI to
    # suggest. Free-text — the renderer accepts any {{key}} that the
    # admin types and substitutes from the employee context.
    placeholders: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )

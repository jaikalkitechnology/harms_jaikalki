from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args


class SavedReport(Base, TimestampMixin):
    """A user-defined report definition that can be re-run on demand."""

    __tablename__ = "report_saved"
    __table_args__ = (
        UniqueConstraint("code", name="uq_saved_report_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_type: Mapped[str] = mapped_column(
        Enum(
            "headcount",
            "attrition",
            "attendance",
            "payroll_cost",
            "compliance",
            "sales",
            "performance",
            "verification",
            "training",
            "custom",
            name="report_type",
        ),
        default="custom",
        nullable=False,
    )
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    schedule_recipients: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Optional uploaded artefact: PDF, ZIP, XLSX, etc. Set when an admin
    # attaches a generated report file. file_size in bytes; file_mime is
    # the original Content-Type so the UI can show the right icon.
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_mime: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

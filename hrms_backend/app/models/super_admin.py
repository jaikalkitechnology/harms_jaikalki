"""Phase 4.5 super-admin models — system config, modules, branding,
backups, API keys, email templates."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args


class SystemConfig(Base, TimestampMixin):
    """Key/value bag for runtime-mutable settings (SMTP, SMS, storage,
    security policy, etc.). The category column groups related keys for
    the UI."""

    __tablename__ = "system_configs"
    __table_args__ = (
        UniqueConstraint("key", name="uq_system_config_key"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), nullable=False, default="general", index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ModuleSetting(Base, TimestampMixin):
    """Per-module enable/disable + config. Module codes match what the
    mobile app reads via /api/v1/launch/modules to hide screens."""

    __tablename__ = "module_settings"
    __table_args__ = (
        UniqueConstraint("module_code", name="uq_module_setting_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_core: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Core modules cannot be disabled.",
    )
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class BrandingSettings(Base, TimestampMixin):
    """Singleton row holding the white-label config. We keep a row per
    company_id to leave the door open for multi-tenant; today only id=1
    is used."""

    __tablename__ = "branding_settings"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(
        String(16), default="#1f2937", nullable=False
    )
    secondary_color: Mapped[str] = mapped_column(
        String(16), default="#b45309", nullable=False
    )
    font_family: Mapped[str] = mapped_column(
        String(64), default="Inter", nullable=False
    )
    login_background_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    custom_domain: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    extras: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class DatabaseBackup(Base, TimestampMixin):
    """Tracks backup files produced by `scripts/ops/backup.sh` (or the
    on-demand admin trigger). The actual file lives at file_path on disk
    or in object storage; this row is the catalogue."""

    __tablename__ = "database_backups"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default="completed", nullable=False, index=True,
        comment="completed | failed | running",
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


class ApiKey(Base, TimestampMixin):
    """Hashed API tokens for partner integrations. The plain key is shown
    only once at creation and never re-readable."""

    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_api_key_hash"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    key_prefix: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="First 8 chars of the plain key for UI display.",
    )
    scopes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class EmailTemplate(Base, TimestampMixin):
    """Editable transactional templates. The `code` is the key the email
    service uses to look one up; `body_html` supports {{variable}}
    placeholders rendered server-side."""

    __tablename__ = "email_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_email_template_code"),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variables: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

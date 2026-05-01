from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(191), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin_portal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)

    designation_id: Mapped[int | None] = mapped_column(
        ForeignKey("designations.id", ondelete="SET NULL"), nullable=True
    )

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    roles: Mapped[List["UserRole"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def role_codes(self) -> list[str]:
        return [ur.role.code for ur in self.roles if ur.role]

    @property
    def max_role_level(self) -> int:
        levels = [ur.role.level for ur in self.roles if ur.role]
        return max(levels) if levels else 0

    @property
    def permission_codes(self) -> list[str]:
        codes: set[str] = set()
        for ur in self.roles:
            if not ur.role:
                continue
            for rp in ur.role.permissions:
                if rp.permission:
                    codes.add(rp.permission.code)
        return sorted(codes)

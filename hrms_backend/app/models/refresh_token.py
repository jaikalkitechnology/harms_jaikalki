from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class RefreshToken(Base, TimestampMixin):
    """Tracks issued refresh tokens so we can revoke them on logout."""

    __tablename__ = "refresh_tokens"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Set when this token was exchanged for a new pair (as opposed to a
    # logout). Lets a retry within the grace window succeed.
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(lazy="joined")  # noqa: F821

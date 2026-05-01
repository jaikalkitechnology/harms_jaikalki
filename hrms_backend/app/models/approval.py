from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, mysql_table_args


class ApprovalWorkflow(Base, TimestampMixin):
    __tablename__ = "approval_workflows"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON list of level definitions:
    # [{"level": 1, "approver_role": "manager", "auto_approve_if": "days <= 1"}, ...]
    levels_config: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conditions_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"
    __table_args__ = (
        UniqueConstraint(
            "request_type", "request_id", name="uq_approval_request"
        ),
        mysql_table_args,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    request_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Subject employee — used for visibility scoping in the universal inbox.
    employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Snapshot of request fields at submission (so the inbox can render
    # without dereferencing the underlying record on every paint).
    request_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    title: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_levels: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "approved",
            "rejected",
            "cancelled",
            "escalated",
            name="approval_status",
        ),
        default="pending",
        nullable=False,
        index=True,
    )

    initiated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    final_status: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    final_decision_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    actions: Mapped[list["ApprovalAction"]] = relationship(
        back_populates="approval",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ApprovalAction.action_at",
    )


class ApprovalAction(Base):
    __tablename__ = "approval_actions"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approval_id: Mapped[int] = mapped_column(
        ForeignKey("approvals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    approver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        Enum(
            "approved",
            "rejected",
            "delegated",
            "commented",
            "cancelled",
            name="approval_action_kind",
        ),
        nullable=False,
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delegated_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    approval: Mapped["Approval"] = relationship(back_populates="actions")

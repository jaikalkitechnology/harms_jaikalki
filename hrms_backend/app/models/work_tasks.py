"""Tasks a manager assigns to people in their team (or anyone notes for
themselves). Overdue tasks are escalated up the reporting chain."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, mysql_table_args

TASK_PRIORITIES = ("low", "medium", "high", "urgent")
TASK_STATUSES = ("open", "in_progress", "done", "cancelled")
OPEN_STATUSES = ("open", "in_progress")


class WorkTask(Base, TimestampMixin):
    __tablename__ = "work_tasks"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The employee who gave the task (None when HR without an employee
    # record assigned it); created_by is the login that did it.
    assigned_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completion_note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    # 0 = not escalated; 1 = assigner reminded; 2+ = sent further up.
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class WorkTaskComment(Base, TimestampMixin):
    __tablename__ = "work_task_comments"
    __table_args__ = mysql_table_args

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("work_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

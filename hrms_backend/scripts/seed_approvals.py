"""Seed default approval workflows.

Run after seed_employees.py / seed_attendance_leave.py:

    python -m scripts.seed_approvals
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import ApprovalWorkflow


WORKFLOWS = [
    {
        "type": "leave_request",
        "name": "Leave Request",
        "description": "Single-level approval by direct manager / HR.",
        "levels_config": [
            {
                "level": 1,
                "approver_role": "manager",
                "permission": "leave.approve.team",
            },
        ],
        "conditions_json": {"escalate_after_days": 3},
    },
    {
        "type": "attendance_regularization",
        "name": "Attendance Regularization",
        "description": "Single-level approval by manager / HR.",
        "levels_config": [
            {"level": 1, "approver_role": "manager", "permission": "approval.act"},
        ],
        "conditions_json": None,
    },
    {
        "type": "intern_expense",
        "name": "Intern Travel Expense",
        "description": "Single-level approval by HR / manager / admin.",
        "levels_config": [
            {"level": 1, "approver_role": "manager", "permission": "approval.act"},
        ],
        "conditions_json": None,
    },
]


async def seed_workflows(db: AsyncSession) -> None:
    existing = {
        w.type: w
        for w in (await db.execute(select(ApprovalWorkflow))).scalars().all()
    }
    for spec in WORKFLOWS:
        if spec["type"] in existing:
            continue
        db.add(ApprovalWorkflow(**spec, is_active=True))
    await db.flush()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed_workflows(db)
        await db.commit()
    print(f"✔ Seeded {len(WORKFLOWS)} approval workflows")


if __name__ == "__main__":
    asyncio.run(run())

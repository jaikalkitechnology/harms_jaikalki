"""Seed 9 department-specific DWP templates (morning + EOD).

Run after seed_employees.py:

    python -m scripts.seed_dwp
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Department, DwpTemplate, DwpTemplateField


# Common morning fields shared across templates.
MORNING_BASE_FIELDS = [
    {
        "key": "tasks",
        "label": "Tasks for today",
        "field_type": "textarea",
        "is_required": True,
        "help_text": "List the work items you'll tackle today.",
    },
    {
        "key": "hours_planned",
        "label": "Hours planned",
        "field_type": "number",
        "is_required": False,
    },
    {
        "key": "help_needed",
        "label": "Need help with?",
        "field_type": "textarea",
        "is_required": False,
        "help_text": "Anything blocking you or where you'd like input.",
    },
    {
        "key": "status_tag",
        "label": "Status",
        "field_type": "select",
        "options": ["green", "yellow", "red"],
        "is_required": False,
    },
]

# Common EOD fields.
EOD_BASE_FIELDS = [
    {
        "key": "tasks",
        "label": "Tasks completed",
        "field_type": "textarea",
        "is_required": True,
    },
    {
        "key": "completion_pct",
        "label": "Completion %",
        "field_type": "percent",
        "is_required": False,
    },
    {
        "key": "blockers",
        "label": "Blockers",
        "field_type": "textarea",
        "is_required": False,
        "help_text": "Anything blocking progress your manager should know about.",
    },
    {
        "key": "hours_actual",
        "label": "Hours worked",
        "field_type": "number",
        "is_required": False,
    },
    {
        "key": "mood_rating",
        "label": "How did the day feel?",
        "field_type": "rating",
        "is_required": False,
    },
    {
        "key": "tomorrow_plan",
        "label": "Tomorrow's plan",
        "field_type": "textarea",
        "is_required": False,
    },
]


# Department-specific extras.
EXTRA_FIELDS: dict[str, dict[str, list]] = {
    "IT": {
        "morning": [
            {"key": "project", "label": "Primary project", "field_type": "text", "is_required": False},
        ],
        "eod": [
            {"key": "prs_opened", "label": "PRs opened", "field_type": "number", "is_required": False},
        ],
    },
    "SAL": {
        "morning": [
            {"key": "calls_planned", "label": "Calls planned", "field_type": "number", "is_required": False},
            {"key": "demos_planned", "label": "Demos planned", "field_type": "number", "is_required": False},
        ],
        "eod": [
            {"key": "calls_made", "label": "Calls made", "field_type": "number", "is_required": False},
            {"key": "deals_closed", "label": "Deals closed", "field_type": "number", "is_required": False},
        ],
    },
    "OPS": {
        "morning": [
            {"key": "tickets_in_queue", "label": "Tickets in queue", "field_type": "number", "is_required": False},
        ],
        "eod": [
            {"key": "tickets_resolved", "label": "Tickets resolved", "field_type": "number", "is_required": False},
        ],
    },
}


# Templates definition. Code suffix `-M` for morning, `-E` for EOD.
TEMPLATES = [
    ("DWP-IT", "IT / Development", "IT"),
    ("DWP-SALES", "Sales", "SAL"),
    ("DWP-OPS", "Customer Support / Ops", "OPS"),
    ("DWP-DESIGN", "Design", None),  # global fallback if no DESIGN dept seeded
    ("DWP-MKT", "Marketing", None),
    ("DWP-HR", "HR / Admin", "HR"),
    ("DWP-HOUSE", "Housekeeping", None),
    ("DWP-FIELD", "Field Force", None),
    ("DWP-PROD", "Production", None),
]


async def seed_templates(db: AsyncSession) -> None:
    departments = {
        d.code: d for d in (await db.execute(select(Department))).scalars().all()
    }
    existing = {
        t.code: t for t in (await db.execute(select(DwpTemplate))).scalars().all()
    }

    # Make the IT morning template the global fallback so any employee
    # without a department-specific template still gets something useful.
    for code, name, dept_code in TEMPLATES:
        for variant in ("morning", "eod"):
            full_code = f"{code}-{'M' if variant == 'morning' else 'E'}"
            if full_code in existing:
                continue
            dept = departments.get(dept_code) if dept_code else None
            tpl = DwpTemplate(
                code=full_code,
                name=f"{name} — {variant.capitalize()}",
                description=f"Default {variant} DWP template for {name}.",
                department_id=dept.id if dept else None,
                type=variant,
                is_active=True,
            )
            db.add(tpl)
            await db.flush()

            base = MORNING_BASE_FIELDS if variant == "morning" else EOD_BASE_FIELDS
            extras = EXTRA_FIELDS.get(dept_code or "", {}).get(variant, [])
            for i, spec in enumerate(base + extras):
                db.add(
                    DwpTemplateField(
                        template_id=tpl.id,
                        key=spec["key"],
                        label=spec["label"],
                        field_type=spec["field_type"],
                        is_required=spec.get("is_required", False),
                        options=spec.get("options"),
                        help_text=spec.get("help_text"),
                        display_order=i,
                    )
                )
            existing[full_code] = tpl

    # Promote one template (IT morning + EOD) to dept_id=NULL so it acts as
    # the global default if a department doesn't have a specific one.
    # We do this by inserting a single global pair if it doesn't already exist.
    for variant, suffix in (("morning", "M"), ("eod", "E")):
        global_code = f"DWP-DEFAULT-{suffix}"
        if global_code in existing:
            continue
        tpl = DwpTemplate(
            code=global_code,
            name=f"Default — {variant.capitalize()}",
            description="Global fallback DWP template.",
            department_id=None,
            type=variant,
            is_active=True,
        )
        db.add(tpl)
        await db.flush()
        base = MORNING_BASE_FIELDS if variant == "morning" else EOD_BASE_FIELDS
        for i, spec in enumerate(base):
            db.add(
                DwpTemplateField(
                    template_id=tpl.id,
                    key=spec["key"],
                    label=spec["label"],
                    field_type=spec["field_type"],
                    is_required=spec.get("is_required", False),
                    options=spec.get("options"),
                    help_text=spec.get("help_text"),
                    display_order=i,
                )
            )
        existing[global_code] = tpl

    await db.flush()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed_templates(db)
        await db.commit()
    print(f"✔ Seeded DWP templates ({len(TEMPLATES)} dept variants × 2 + global fallback)")


if __name__ == "__main__":
    asyncio.run(run())

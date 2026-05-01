"""Seed verification: address + employment templates + 2 jobs for JKT019."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Employee, Verification, VerificationTemplate


ADDRESS_TEMPLATE = dict(
    code="VT-ADDRESS-V1",
    name="Address Verification (Residential)",
    type="address",
    description="Standard residential address verification",
    fields=[
        {"key": "person_met", "label": "Person met", "field_type": "text", "required": True},
        {"key": "relation", "label": "Relation", "field_type": "dropdown",
         "required": True,
         "options": ["self", "spouse", "parent", "sibling", "neighbour", "landlord", "other"]},
        {"key": "duration_at_address", "label": "Years at address",
         "field_type": "number", "required": True},
        {"key": "ownership", "label": "Ownership", "field_type": "dropdown",
         "required": True,
         "options": ["owned", "rented", "company-provided", "other"]},
        {"key": "address_type", "label": "Property type",
         "field_type": "dropdown", "required": True,
         "options": ["independent_house", "apartment", "shared", "pg"]},
        {"key": "neighbour_remarks", "label": "Neighbour remarks",
         "field_type": "textarea", "required": False},
    ],
    photo_requirements=[
        {"key": "house_front", "label": "House front", "required": True},
        {"key": "name_plate", "label": "Name plate / unit number", "required": True},
        {"key": "address_proof", "label": "Address proof document", "required": False},
    ],
    signature_required=True,
    sla_hours=48,
)

EMPLOYMENT_TEMPLATE = dict(
    code="VT-EMPLOY-V1",
    name="Employment Verification",
    type="employment",
    description="Verifies current/past employment claims",
    fields=[
        {"key": "company_name", "label": "Company name", "field_type": "text", "required": True},
        {"key": "designation", "label": "Designation",
         "field_type": "text", "required": True},
        {"key": "joining_date", "label": "Joining date",
         "field_type": "date", "required": True},
        {"key": "exit_date", "label": "Exit date (if applicable)",
         "field_type": "date", "required": False},
        {"key": "verifier_name", "label": "HR/Verifier contacted",
         "field_type": "text", "required": True},
        {"key": "verifier_designation", "label": "Verifier designation",
         "field_type": "text", "required": True},
    ],
    photo_requirements=[
        {"key": "company_signage", "label": "Company signage / reception",
         "required": True},
    ],
    signature_required=False,
    sla_hours=72,
)

DOCUMENT_TEMPLATE = dict(
    code="VT-DOC-V1",
    name="Document Verification (PAN/Aadhaar)",
    type="document",
    description="Physical document verification with copy capture",
    fields=[
        {"key": "document_type", "label": "Document type",
         "field_type": "dropdown", "required": True,
         "options": ["pan", "aadhaar", "driving_license", "voter_id", "passport"]},
        {"key": "document_number", "label": "Document number",
         "field_type": "text", "required": True},
        {"key": "name_match", "label": "Name matches subject?",
         "field_type": "checkbox", "required": True},
        {"key": "tamper_check", "label": "Tamper check passed?",
         "field_type": "checkbox", "required": True},
    ],
    photo_requirements=[
        {"key": "document_front", "label": "Document front", "required": True},
        {"key": "document_back", "label": "Document back", "required": False},
    ],
    signature_required=False,
    sla_hours=24,
)


async def seed_templates(db: AsyncSession) -> dict[str, VerificationTemplate]:
    existing = {
        t.code: t
        for t in (await db.execute(select(VerificationTemplate))).scalars().all()
    }
    out = {}
    for spec in (ADDRESS_TEMPLATE, EMPLOYMENT_TEMPLATE, DOCUMENT_TEMPLATE):
        t = existing.get(spec["code"])
        if not t:
            t = VerificationTemplate(**spec, is_active=True)
            db.add(t)
            await db.flush()
        out[spec["code"]] = t
    return out


async def seed_jobs(
    db: AsyncSession, templates: dict[str, VerificationTemplate]
) -> None:
    emp = (
        await db.execute(
            select(Employee).where(Employee.employee_code == "JKT019")
        )
    ).scalar_one_or_none()
    if not emp:
        return

    existing = (
        await db.execute(
            select(Verification).where(Verification.assigned_to == emp.id)
        )
    ).scalars().all()
    if existing:
        return

    now = datetime.utcnow()
    specs = [
        dict(
            ticket_number="JKT/V/2026/00001",
            template_id=templates["VT-ADDRESS-V1"].id,
            type="address",
            subject_name="Rohit Sharma",
            subject_data={
                "dob": "1992-03-14",
                "father_name": "Anil Sharma",
                "applicant_id": "APP-2026-1023",
            },
            address="44, 1st Cross, JP Nagar 7th Phase, Bengaluru 560078",
            contact_phone="+91-9000000010",
            requested_by_org="Trustline Banking Services",
            assigned_to=emp.id,
            assigned_at=now,
            deadline_at=now + timedelta(hours=48),
            status="pending",
        ),
        dict(
            ticket_number="JKT/V/2026/00002",
            template_id=templates["VT-EMPLOY-V1"].id,
            type="employment",
            subject_name="Priya Mehta",
            subject_data={
                "claimed_company": "Sunrise Logistics",
                "claimed_designation": "Operations Lead",
                "applicant_id": "APP-2026-1024",
            },
            address="Sunrise Logistics, Whitefield, Bengaluru",
            contact_phone="+91-9000000011",
            requested_by_org="Sigma Capital",
            assigned_to=emp.id,
            assigned_at=now,
            deadline_at=now + timedelta(hours=72),
            status="pending",
        ),
    ]
    for spec in specs:
        db.add(Verification(**spec))
    await db.flush()


async def seed(db: AsyncSession) -> None:
    templates = await seed_templates(db)
    await seed_jobs(db, templates)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)
        await db.commit()
    print("✔ Verification seeded (3 templates, 2 jobs)")


if __name__ == "__main__":
    asyncio.run(run())

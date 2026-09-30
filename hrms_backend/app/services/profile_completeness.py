"""Employee profile completeness — which records HR still has to fill.

Each check has a stable key the admin UI uses to jump to the section
that fixes it. Checks that don't apply to an employee (bank and UAN for
an unpaid intern, UAN for a PF opt-out) are left out rather than
counted as done, so the score reflects only what that person needs.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Employee, EmployeeBankDetails, EmployeeDocument, EmployeeNominee

# key, label, section (profile tab the UI opens to fix it)
CHECKS: list[tuple[str, str, str]] = [
    ("photo", "Profile photo", "overview"),
    ("date_of_birth", "Date of birth", "personal"),
    ("gender", "Gender", "personal"),
    ("personal_phone", "Personal phone", "personal"),
    ("personal_email", "Personal email", "personal"),
    ("job", "Department & designation", "overview"),
    ("manager", "Reporting manager", "overview"),
    ("salary", "Salary template & CTC", "pay"),
    ("bank", "Bank account", "pay"),
    ("uan", "UAN number", "statutory"),
    ("nominee", "Nominee", "personal"),
    ("doc_aadhaar", "Aadhaar card", "documents"),
    ("doc_pan", "PAN card", "documents"),
    ("doc_bank", "Bank passbook / cancelled cheque", "documents"),
]

def _checks_for(
    e: Employee, *, has_bank: bool, has_nominee: bool, docs: set[str]
) -> dict[str, bool]:
    cat = e.category
    paid = bool(cat is None or cat.has_salary)
    pf_applies = paid and not e.pf_opt_out and (cat is None or cat.eligible_for_pf)

    out: dict[str, bool] = {
        "photo": bool(e.photo_url),
        "date_of_birth": e.date_of_birth is not None,
        "gender": bool(e.gender),
        "personal_phone": bool(e.personal_phone),
        "personal_email": bool(e.personal_email),
        "job": e.department_id is not None and e.designation_id is not None,
        "manager": e.reporting_to is not None,
        "nominee": has_nominee,
        "doc_aadhaar": "aadhaar" in docs,
        "doc_pan": "pan" in docs,
    }
    if paid:
        out["salary"] = e.salary_template_id is not None and bool(e.ctc_annual)
        out["bank"] = has_bank
        out["doc_bank"] = bool(docs & {"bank_passbook", "cancelled_cheque"})
    if pf_applies:
        out["uan"] = bool((e.uan_number or "").strip())
    return out


def _summary(employee_id: int, checks: dict[str, bool]) -> dict:
    items = [
        {"key": k, "label": label, "section": section, "done": checks[k]}
        for k, label, section in CHECKS
        if k in checks
    ]
    done = sum(1 for i in items if i["done"])
    total = len(items)
    return {
        "employee_id": employee_id,
        "done": done,
        "total": total,
        "percent": round(done * 100 / total) if total else 100,
        "missing": [i for i in items if not i["done"]],
        "items": items,
    }


async def completeness(
    db: AsyncSession, employees: Iterable[Employee]
) -> dict[int, dict]:
    """Completeness for each employee, in three grouped queries."""
    emps = list(employees)
    ids = [e.id for e in emps]
    if not ids:
        return {}

    banks = set(
        (
            await db.execute(
                select(EmployeeBankDetails.employee_id).where(
                    EmployeeBankDetails.employee_id.in_(ids)
                )
            )
        ).scalars()
    )
    nominees = set(
        (
            await db.execute(
                select(EmployeeNominee.employee_id)
                .where(EmployeeNominee.employee_id.in_(ids))
                .distinct()
            )
        ).scalars()
    )
    docs: dict[int, set[str]] = defaultdict(set)
    for emp_id, doc_type in (
        await db.execute(
            select(EmployeeDocument.employee_id, EmployeeDocument.doc_type)
            .where(EmployeeDocument.employee_id.in_(ids))
            .distinct()
        )
    ).all():
        docs[emp_id].add(doc_type)

    return {
        e.id: _summary(
            e.id,
            _checks_for(
                e,
                has_bank=e.id in banks,
                has_nominee=e.id in nominees,
                docs=docs[e.id],
            ),
        )
        for e in emps
    }

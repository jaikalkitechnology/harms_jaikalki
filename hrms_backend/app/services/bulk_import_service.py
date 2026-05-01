"""Employee bulk import via CSV.

Required columns:
  first_name, last_name, employment_type, date_of_joining,
  category_code

Optional columns:
  email, work_location, ctc_annual, designation_code,
  department_code, reporting_to_code, work_mode, gender, personal_phone,
  date_of_birth

A row that fails validation is reported with its row number — the rest
of the import keeps going so a single bad row doesn't block 99 good ones.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department, Designation, Employee
from app.schemas.employee import EmployeeCreate
from app.services import employee_service


REQUIRED_COLUMNS = {
    "first_name",
    "last_name",
    "employment_type",
    "date_of_joining",
    "category_code",
}


def _parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value: str) -> Optional[Decimal]:
    if not value or not value.strip():
        return None
    try:
        return Decimal(value.replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


async def _resolve_codes(
    db: AsyncSession, *, department_code: Optional[str], designation_code: Optional[str]
) -> tuple[Optional[int], Optional[int]]:
    dep_id = None
    des_id = None
    if department_code:
        d = (
            await db.execute(
                select(Department).where(Department.code == department_code)
            )
        ).scalar_one_or_none()
        dep_id = d.id if d else None
    if designation_code:
        d = (
            await db.execute(
                select(Designation).where(Designation.code == designation_code)
            )
        ).scalar_one_or_none()
        des_id = d.id if d else None
    return dep_id, des_id


async def _resolve_manager(
    db: AsyncSession, code: Optional[str]
) -> Optional[int]:
    if not code:
        return None
    e = (
        await db.execute(
            select(Employee).where(Employee.employee_code == code)
        )
    ).scalar_one_or_none()
    return e.id if e else None


async def import_employees_csv(
    db: AsyncSession,
    *,
    csv_bytes: bytes,
) -> dict[str, Any]:
    """Returns a dict with total / created / errors."""
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {
            "total": 0,
            "created": 0,
            "errors": [{"row": 0, "error": "empty CSV"}],
        }
    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        return {
            "total": 0,
            "created": 0,
            "errors": [
                {
                    "row": 0,
                    "error": f"missing required columns: {', '.join(sorted(missing))}",
                }
            ],
        }

    total = 0
    created = 0
    errors: list[dict[str, Any]] = []

    for i, raw in enumerate(reader, start=2):  # row 1 is the header
        total += 1
        row = {k: (v or "").strip() for k, v in raw.items()}
        try:
            doj = _parse_date(row["date_of_joining"])
            if not doj:
                raise ValueError(
                    f"invalid date_of_joining: {row['date_of_joining']!r}"
                )
            dep_id, des_id = await _resolve_codes(
                db,
                department_code=row.get("department_code") or None,
                designation_code=row.get("designation_code") or None,
            )
            mgr_id = await _resolve_manager(
                db, row.get("reporting_to_code") or None
            )
            payload = EmployeeCreate(
                first_name=row["first_name"],
                last_name=row["last_name"],
                employment_type=row["employment_type"] or "full_time",
                date_of_joining=doj,
                category_code=row["category_code"],
                ctc_annual=_parse_decimal(row.get("ctc_annual", "")),
                department_id=dep_id,
                designation_id=des_id,
                reporting_to=mgr_id,
                work_location=row.get("work_location") or None,
                work_mode=row.get("work_mode") or "office",
                gender=row.get("gender") or None,
                personal_phone=row.get("personal_phone") or None,
                personal_email=row.get("email") or None,
                date_of_birth=_parse_date(row.get("date_of_birth", "")),
                create_user_account=bool(row.get("email")),
                user_email=row.get("email") or None,
            )
            await employee_service.create_employee(db, payload)
            created += 1
        except Exception as exc:
            errors.append(
                {"row": i, "error": f"{exc.__class__.__name__}: {exc}"}
            )
            # roll back this row's failure so the next one runs cleanly
            await db.rollback()

    return {"total": total, "created": created, "errors": errors}

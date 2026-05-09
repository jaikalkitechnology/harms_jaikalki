"""Import historical attendance from `attendance_data/Jaikalki - Attendance Sheet 2025.xlsx`.

Run after seed_employees.py / seed_attendance_leave.py:

    python -m scripts.seed_attendance_history

Behaviour
---------
1.  Reads every monthly sheet (`Jan '25` → `Jun '26`).
2.  Auto-creates any employees from the workbook that don't yet exist
    in the DB. The first 11 of those (JKT001..JKT011) are slotted into
    the PERMANENT category with the JKT-PERM-L2 template; JKT012 and
    onward use the same defaults but can be tuned afterwards by HR.
3.  Walks days 1..31 for each employee row and upserts an Attendance
    row keyed on (employee_id, date):
        P → status='present', source='import'
        L → status='leave',   source='import'
        H → skipped (the Holiday table covers those)
        empty → skipped (we don't fabricate 'absent')
4.  After the import, any employee whose last 'P' is more than
    `--gap-days N` days ago (default 60) gets marked
    `status='resigned'`, `exit_date=last_present_date`, and a
    Resignation row is created in `cleared` state with the reason
    "Auto-derived from attendance import — no presence after {date}".

Idempotent. Re-running adjusts existing rows in place.
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Attendance,
    Employee,
    EmployeeCategory,
    Resignation,
    SalaryTemplate,
)


XLSX_PATH = Path("attendance_data/Jaikalki - Attendance Sheet 2025.xlsx")

# Map sheet name → (year, month). Sheet names are like "Jan '25" / "Apr '26".
_MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11, "novemeber": 11,  # workbook typo
    "dec": 12, "december": 12,
}


def _parse_sheet_name(name: str) -> Optional[tuple[int, int]]:
    """`Jan '25` → (2025, 1). Returns None if unrecognised."""
    s = name.strip()
    m = re.match(r"^([A-Za-z\.]+)\s*'?(\d{2,4})$", s)
    if not m:
        return None
    mname = m.group(1).strip(".").lower()
    yr = int(m.group(2))
    if yr < 100:
        yr += 2000
    return (yr, _MONTH_NAMES.get(mname))


# ── Date-of-joining string parser  ────────────────────────────────────
# The spreadsheet stores DOJ as e.g. "14th Sept 2024" or "30th Jan 2025".
_DOJ_RE = re.compile(
    r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z\.]+)\s+(\d{4})$"
)


def _parse_doj(raw: object) -> Optional[date]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()
    m = _DOJ_RE.match(s)
    if not m:
        return None
    day = int(m.group(1))
    mname = m.group(2).strip(".").lower()
    yr = int(m.group(3))
    mnum = _MONTH_NAMES.get(mname)
    if mnum is None:
        return None
    try:
        return date(yr, mnum, day)
    except ValueError:
        return None


# ── Workbook → in-memory rows ─────────────────────────────────────────
def read_workbook(path: Path) -> dict:
    """Returns
    {
        'employees': {code: {'name': str, 'doj': date|None}},
        'attendance': [(code, year, month, day, marker), ...],
    }
    """
    try:
        from openpyxl import load_workbook
    except ImportError as e:
        raise RuntimeError(
            "openpyxl is required to import the attendance workbook. "
            "Install it with: pip install openpyxl"
        ) from e

    wb = load_workbook(filename=str(path), data_only=True, read_only=True)
    employees: dict[str, dict] = {}
    rows: list[tuple[str, int, int, int, str]] = []

    for sheet_name in wb.sheetnames:
        ym = _parse_sheet_name(sheet_name)
        if ym is None or ym[1] is None:
            print(f"  · skipping unrecognised sheet: {sheet_name!r}")
            continue
        year, month = ym

        ws = wb[sheet_name]
        all_rows = list(ws.iter_rows(values_only=True))
        if len(all_rows) < 8:
            continue

        # Header row 5 (1-indexed) holds the date numbers in cols 6..36.
        # all_rows is 0-indexed → index 4.
        date_row = all_rows[4]

        # Build a column → day-of-month mapping.
        col_to_day: dict[int, int] = {}
        for col_idx, cell in enumerate(date_row):
            if isinstance(cell, int) and 1 <= cell <= 31:
                col_to_day[col_idx] = cell

        for r in all_rows[7:]:
            if not r or r[0] is None:
                continue
            code = str(r[0]).strip()
            if not code.startswith("JKT") or len(code) != 6:
                continue
            name = (str(r[1]).strip() if r[1] else "")
            doj = _parse_doj(r[3])
            if code not in employees:
                employees[code] = {"name": name, "doj": doj}
            else:
                # Keep the earliest non-empty doj/name.
                if not employees[code].get("name") and name:
                    employees[code]["name"] = name
                if not employees[code].get("doj") and doj:
                    employees[code]["doj"] = doj

            for col_idx, day_n in col_to_day.items():
                cell = r[col_idx] if col_idx < len(r) else None
                if cell is None:
                    continue
                marker = str(cell).strip().upper()
                if not marker:
                    continue
                # Validate the date is real (Feb 30 etc. just won't roll up).
                try:
                    _ = date(year, month, day_n)
                except ValueError:
                    continue
                rows.append((code, year, month, day_n, marker))

    return {"employees": employees, "attendance": rows}


# ── DB-side helpers ──────────────────────────────────────────────────
async def _ensure_employee(
    db: AsyncSession,
    *,
    code: str,
    name: str,
    doj: Optional[date],
    permanent_cat_id: int,
    default_template_id: int,
) -> Employee:
    existing = (
        await db.execute(select(Employee).where(Employee.employee_code == code))
    ).scalar_one_or_none()
    if existing is not None:
        # Backfill DOJ if the seed didn't have one, but never clobber a real value.
        if doj and not existing.date_of_joining:
            existing.date_of_joining = doj
        return existing

    parts = name.split(maxsplit=1) if name else [code, ""]
    first = parts[0] or code
    last = parts[1] if len(parts) > 1 else ""

    emp = Employee(
        employee_code=code,
        first_name=first,
        last_name=last,
        category_id=permanent_cat_id,
        salary_template_id=default_template_id,
        date_of_joining=doj or date(2025, 1, 1),
        is_on_probation=False,
        status="active",
        ctc_annual=Decimal("300000"),
    )
    db.add(emp)
    await db.flush()
    return emp


async def _upsert_attendance(
    db: AsyncSession,
    *,
    employee_id: int,
    on: date,
    status_: str,
) -> None:
    existing = (
        await db.execute(
            select(Attendance)
            .where(Attendance.employee_id == employee_id)
            .where(Attendance.date == on)
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Attendance(
                employee_id=employee_id,
                date=on,
                status=status_,
                work_mode="office",
                source="import",
            )
        )
    else:
        # Don't overwrite admin-edited / GPS-punched real rows; only
        # touch rows whose source is also `import` (or default).
        if existing.source in ("import", "manual"):
            existing.status = status_
            existing.source = "import"


async def _maybe_resign(
    db: AsyncSession,
    *,
    emp: Employee,
    last_present: Optional[date],
    today: date,
    gap_days: int,
) -> bool:
    if emp.status != "active":
        return False
    if last_present is None:
        # Never present in the workbook range — leave them active so HR
        # can investigate; auto-resigning a no-show is too aggressive.
        return False
    gap = (today - last_present).days
    if gap < gap_days:
        return False

    emp.status = "resigned"
    emp.exit_date = last_present

    # Add or update a Resignation row.
    existing_resig = (
        await db.execute(
            select(Resignation).where(Resignation.employee_id == emp.id)
        )
    ).scalar_one_or_none()
    reason = (
        "Auto-derived from attendance import — no presence after "
        f"{last_present.isoformat()}."
    )
    if existing_resig is None:
        db.add(
            Resignation(
                employee_id=emp.id,
                requested_at=datetime.combine(last_present, datetime.min.time()),
                proposed_last_working_day=last_present,
                actual_last_working_day=last_present,
                reason=reason,
                status="cleared",
                notice_period_days=0,
                hr_cleared_at=datetime.utcnow(),
            )
        )
    else:
        # Refresh dates if we're already tracking one.
        existing_resig.actual_last_working_day = last_present
        existing_resig.proposed_last_working_day = last_present
        existing_resig.status = "cleared"
        if not existing_resig.hr_cleared_at:
            existing_resig.hr_cleared_at = datetime.utcnow()
        if not existing_resig.reason:
            existing_resig.reason = reason
    return True


# ── Main flow ────────────────────────────────────────────────────────
async def main(*, gap_days: int, dry_run: bool, path: Path) -> None:
    if not path.exists():
        print(f"!! Workbook not found at {path}", file=sys.stderr)
        sys.exit(2)

    print(f"→ Reading {path}")
    wb_data = read_workbook(path)
    employees_in_wb = wb_data["employees"]
    attendance_rows = wb_data["attendance"]
    print(
        f"  Workbook: {len(employees_in_wb)} employees, "
        f"{len(attendance_rows)} day-marker rows."
    )

    async with AsyncSessionLocal() as db:
        # Resolve PERMANENT category and a default template (JKT-PERM-L2).
        permanent_cat = (
            await db.execute(
                select(EmployeeCategory).where(EmployeeCategory.code == "PERMANENT")
            )
        ).scalar_one_or_none()
        if permanent_cat is None:
            print("!! PERMANENT category missing — run seed_employees first.",
                  file=sys.stderr)
            sys.exit(2)

        default_template = (
            await db.execute(
                select(SalaryTemplate).where(SalaryTemplate.template_code == "JKT-PERM-L2")
            )
        ).scalar_one_or_none()
        if default_template is None:
            print("!! JKT-PERM-L2 template missing — run seed_employees first.",
                  file=sys.stderr)
            sys.exit(2)

        # 1. Ensure each spreadsheet employee exists.
        emp_by_code: dict[str, Employee] = {}
        created = 0
        for code, info in sorted(employees_in_wb.items()):
            emp = await _ensure_employee(
                db,
                code=code,
                name=info["name"],
                doj=info["doj"],
                permanent_cat_id=permanent_cat.id,
                default_template_id=default_template.id,
            )
            if emp.id is None:
                # New row — flush so it gets an id.
                await db.flush()
            emp_by_code[code] = emp
            if emp.id and emp.created_at is None:
                created += 1
        print(f"  Employees: {created} new, {len(emp_by_code) - created} existing.")

        # 2. Upsert attendance rows.
        last_present: dict[str, date] = {}
        upserted = 0
        skipped = 0
        for code, year, month, day_n, marker in attendance_rows:
            emp = emp_by_code.get(code)
            if emp is None:
                skipped += 1
                continue
            try:
                d = date(year, month, day_n)
            except ValueError:
                skipped += 1
                continue
            if marker == "P":
                await _upsert_attendance(
                    db, employee_id=emp.id, on=d, status_="present"
                )
                upserted += 1
                if code not in last_present or d > last_present[code]:
                    last_present[code] = d
            elif marker == "L":
                await _upsert_attendance(
                    db, employee_id=emp.id, on=d, status_="leave"
                )
                upserted += 1
            elif marker == "H":
                # Holiday — already in the Holiday table (or absent from it,
                # in which case admins can add it).
                continue
            else:
                skipped += 1
        print(f"  Attendance: {upserted} rows imported, {skipped} skipped.")

        # 3. Resignation pass.
        today = date.today()
        resigned = []
        for code, emp in emp_by_code.items():
            lp = last_present.get(code)
            if await _maybe_resign(
                db, emp=emp, last_present=lp, today=today, gap_days=gap_days
            ):
                resigned.append((code, emp.first_name + " " + emp.last_name, lp))

        if resigned:
            print(
                f"  Resigned (gap > {gap_days} days, today={today}):"
            )
            for code, name, lp in resigned:
                print(f"    · {code} {name:30s} last_present={lp}")
        else:
            print(f"  No resignations triggered (gap threshold = {gap_days} days).")

        if dry_run:
            print("→ Dry run; rolling back.")
            await db.rollback()
        else:
            await db.commit()
            print("→ Committed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gap-days", type=int, default=60,
        help="Mark employees with no 'P' for this many days as resigned (default 60).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without committing changes.",
    )
    parser.add_argument(
        "--path", type=Path, default=XLSX_PATH,
        help=f"Path to the attendance workbook (default: {XLSX_PATH}).",
    )
    args = parser.parse_args()
    asyncio.run(main(
        gap_days=args.gap_days,
        dry_run=args.dry_run,
        path=args.path,
    ))

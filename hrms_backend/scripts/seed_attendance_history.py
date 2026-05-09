"""Import historical attendance from `attendance_data/Jaikalki - Attendance Sheet 2025.xlsx`.

Run after seed_employees.py / seed_attendance_leave.py:

    python -m scripts.seed_attendance_history
    python -m scripts.seed_attendance_history --dry-run
    python -m scripts.seed_attendance_history --gap-days 90

Behaviour
---------
1.  Drops any leftover demo Employee rows from older seeds
    (JKT014..JKT018). Their User logins (hr@, manager@, employee@,
    pooja@) are *kept* — only the Employee profile is removed. The
    seed_attendance_history flow then re-creates the codes the
    spreadsheet actually uses (which now extend up to JKT015 and
    JKT016 = Anurag).
2.  Reads every monthly sheet (`Jan '25` → `Jun '26`). The workbook
    uses two layouts (Jan-Nov 2025 and Dec 2025 onwards); the parser
    auto-detects the column positions per sheet by locating the
    `Emp. ID`, `Date`, `D O B`, `D O J`, and `D O E` headers.
3.  Person identity = (normalised name, date of joining). Codes can
    be reused in the workbook — JKT011 was Pratibha then Ruma,
    JKT012 was Anupam then Guruprasad. Resolution rule: the LATEST
    occupant of a reused code keeps it, and earlier persons get
    synthetic archival codes JKT-X001, JKT-X002, …. Anurag Randive
    appears without a code in the workbook; we assign him JKT016
    (the first free numeric slot above the spreadsheet's range).
4.  For every person, walks days 1..31 and upserts an Attendance row
    keyed on (employee_id, date):
        P → status='present', source='import'
        L → status='leave',   source='import'
        H → skipped (the Holiday table covers those)
        empty → skipped (we don't fabricate 'absent')
5.  Resignation pass — for every person, if the workbook gives an
    explicit Date-of-Exit (column F in 2026 sheets) we use it. Otherwise
    we fall back to the 60-day-no-presence gap rule (configurable with
    --gap-days). Each resignation flips Employee.status='resigned',
    sets exit_date, and creates a Resignation row in `cleared` state
    with reason "Auto-derived from attendance import — last present
    {date}" or "(DOE per spreadsheet)".

Idempotent. Re-running adjusts existing rows in place.
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections import defaultdict
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


def _resolve_workbook_path() -> Path:
    """Find the attendance workbook regardless of CWD.

    The file lives at <repo_root>/attendance_data/. The script is at
    <repo_root>/hrms_backend/scripts/, so try a few likely positions
    relative to the script's own location, then fall back to the
    plain CWD-relative path so explicit --path overrides still work.
    """
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent.parent / "attendance_data" / "Jaikalki - Attendance Sheet 2025.xlsx",
        here.parent.parent / "attendance_data" / "Jaikalki - Attendance Sheet 2025.xlsx",
        Path("attendance_data") / "Jaikalki - Attendance Sheet 2025.xlsx",
        Path("../attendance_data") / "Jaikalki - Attendance Sheet 2025.xlsx",
    ]
    for c in candidates:
        if c.exists():
            return c
    # No copy on disk — return the canonical relative path so the
    # error message tells the user where it should live.
    return candidates[0]


XLSX_PATH = _resolve_workbook_path()

_DEMO_EMPLOYEE_CODES = {"JKT014", "JKT015", "JKT016", "JKT017", "JKT018"}

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
    mnum = _MONTH_NAMES.get(mname)
    if mnum is None:
        return None
    return (yr, mnum)


_DOJ_RE = re.compile(
    r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z\.]+)\s+(\d{4})$"
)


def _parse_date_string(raw: object) -> Optional[date]:
    """Handles "14th Sept 2024" / "1st Jan 2026" / native date / native datetime."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()
    if not s:
        return None
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


def _norm_name(n: object) -> str:
    return re.sub(r"\s+", " ", str(n or "").strip().lower())


# ── Sheet column detection ───────────────────────────────────────────
def _detect_columns(rows: list) -> Optional[dict]:
    """Locate the relevant columns/rows in a single sheet.

    Returns None if the sheet doesn't have the expected `Emp. ID` /
    `Date` headers (e.g. an unrelated tab).
    """
    id_row = id_col = None
    for r_idx, row in enumerate(rows[:12]):
        for c_idx, cell in enumerate(row or []):
            if cell is None:
                continue
            if str(cell).strip().lower() == "emp. id":
                id_row, id_col = r_idx, c_idx
                break
        if id_row is not None:
            break
    if id_row is None:
        return None

    # Name col is the next non-empty header to the right of Emp. ID.
    name_col = id_col + 1
    header_row = rows[id_row]
    while name_col < len(header_row) and (
        header_row[name_col] is None
        or str(header_row[name_col]).strip() == ""
    ):
        name_col += 1
    if name_col >= len(header_row):
        name_col = id_col + 1

    # Find the row that contains the literal "Date" header — usually
    # 1-3 rows above id_row.
    date_row = date_col = None
    search_lo = max(0, id_row - 4)
    for r_idx in range(search_lo, id_row + 1):
        row = rows[r_idx] or []
        for c_idx, cell in enumerate(row):
            if cell is None:
                continue
            if str(cell).strip().lower() == "date":
                date_row, date_col = r_idx, c_idx
                break
        if date_row is not None:
            break
    if date_row is None:
        return None

    day_1_col = date_col + 1

    # Discover DOB / DOJ / DOE columns within date_row.
    dob_col = doj_col = doe_col = None
    for c_idx, cell in enumerate(rows[date_row] or []):
        if cell is None:
            continue
        s = re.sub(r"\s+", "", str(cell).strip().lower())
        if s == "dob":
            dob_col = c_idx
        elif s == "doj":
            doj_col = c_idx
        elif s == "doj/doe":
            doj_col = c_idx
        elif s == "doe":
            doe_col = c_idx

    return {
        "id_row": id_row,
        "id_col": id_col,
        "name_col": name_col,
        "dob_col": dob_col,
        "doj_col": doj_col,
        "doe_col": doe_col,
        "day_1_col": day_1_col,
    }


# ── Workbook reader ──────────────────────────────────────────────────
def read_workbook(path: Path) -> dict:
    """Returns
    {
        'people': {norm_name: {
                       'name': str, 'doj': date|None, 'doe': date|None,
                       'sheet_codes': [(sheet_idx, raw_code), ...],
                   }, ...},
        'markers': [(norm_name, year, month, day, 'P'|'L'|'H'), ...],
        'sheet_order': [sheet_name, ...],
    }

    Identity key is the normalised name. Some sheets record a slightly
    different DOJ for the same person (Soham Roy: Dec '25 sheet says 18
    Dec, Jan '26 sheet says 29 Dec) — we trust the later sheet because
    those tabs carry the JKT codes and are kept in sync with payroll.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as e:
        raise RuntimeError(
            "openpyxl is required. Install with: pip install openpyxl"
        ) from e

    wb = load_workbook(filename=str(path), data_only=True, read_only=True)
    people: dict[str, dict] = {}
    markers: list[tuple] = []

    sheet_order: list[str] = []

    for sheet_idx, sheet_name in enumerate(wb.sheetnames):
        ym = _parse_sheet_name(sheet_name)
        if ym is None:
            print(f"  · skipping unrecognised sheet: {sheet_name!r}")
            continue
        year, month = ym
        sheet_order.append(sheet_name)

        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        cols = _detect_columns(rows)
        if cols is None:
            print(f"  · skipping {sheet_name}: no Emp. ID/Date headers")
            continue

        # Determine the date columns by scanning the date_row for ints 1..31
        date_row_idx = next(
            (i for i in range(cols["id_row"]) if rows[i] and any(
                str(c).strip().lower() == "date" for c in rows[i] if c is not None
            )),
            None,
        )
        col_to_day: dict[int, int] = {}
        if date_row_idx is not None:
            for c_idx, cell in enumerate(rows[date_row_idx]):
                if isinstance(cell, int) and 1 <= cell <= 31:
                    col_to_day[c_idx] = cell

        # Walk employee rows.
        for r in rows[cols["id_row"] + 1:]:
            if not r:
                continue
            raw_id = r[cols["id_col"]] if cols["id_col"] < len(r) else None
            raw_name = r[cols["name_col"]] if cols["name_col"] < len(r) else None

            code = str(raw_id).strip() if raw_id else ""
            name = str(raw_name).strip() if raw_name else ""
            if not name:
                continue
            if name.lower().startswith("daily attendance"):
                continue

            # Skip non-JKT codes that are clearly stray text (rare).
            if code and not re.match(r"^JKT\d+", code, re.IGNORECASE):
                code = ""

            doj = (
                _parse_date_string(r[cols["doj_col"]])
                if cols["doj_col"] is not None and cols["doj_col"] < len(r)
                else None
            )
            doe = (
                _parse_date_string(r[cols["doe_col"]])
                if cols["doe_col"] is not None and cols["doe_col"] < len(r)
                else None
            )

            key = _norm_name(name)
            entry = people.setdefault(
                key,
                {
                    "name": name,
                    "doj": None,
                    "doe": None,
                    "sheet_codes": [],
                },
            )
            # Use the longest non-truncated name we see.
            if len(name) > len(entry["name"]):
                entry["name"] = name
            # Trust the latest sheet for DOJ/DOE (chronological order).
            if doj:
                entry["doj"] = doj
            if doe:
                entry["doe"] = doe
            entry["sheet_codes"].append((sheet_idx, code or None))

            # Capture day-by-day markers.
            for col_idx, day_n in col_to_day.items():
                if col_idx >= len(r):
                    continue
                cell = r[col_idx]
                if cell is None:
                    continue
                marker = str(cell).strip().upper()
                if marker not in {"P", "L", "H"}:
                    continue
                try:
                    _ = date(year, month, day_n)
                except ValueError:
                    continue
                markers.append((key, year, month, day_n, marker))

    return {
        "people": people,
        "markers": markers,
        "sheet_order": sheet_order,
    }


# ── Code-reuse resolution ────────────────────────────────────────────
def resolve_canonical_codes(
    people: dict[str, dict],
) -> dict[str, str]:
    """Decide the final employee_code each person gets.

    Algorithm:
    - For each person, take the latest non-empty code they were ever
      assigned in the workbook (highest sheet_idx).
    - For codes claimed by multiple persons, the person whose LATEST
      sheet_idx with that code is the highest keeps it. Earlier
      occupants get synthetic JKT-X001, JKT-X002, … codes.
    - Persons with no code at all get the next free numeric slot
      starting at JKT016 (the first slot above the spreadsheet's
      published range).
    """
    # Per-person → latest code (or None) and the sheet_idx of that latest claim.
    latest_claim: dict[str, tuple[Optional[str], int]] = {}
    for key, info in people.items():
        latest_code: Optional[str] = None
        latest_idx = -1
        for sheet_idx, code in info["sheet_codes"]:
            if code and sheet_idx > latest_idx:
                latest_code = code
                latest_idx = sheet_idx
        latest_claim[key] = (latest_code, latest_idx)

    # Code → list of (person_key, latest_idx_for_that_code)
    code_to_claims: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for key, (code, idx) in latest_claim.items():
        if code:
            code_to_claims[code].append((key, idx))

    # Codes claimed by multiple persons need disambiguation.
    canonical: dict[str, str] = {}
    displaced: list[str] = []
    for code, claims in code_to_claims.items():
        # Sort by latest_idx descending; first wins.
        claims.sort(key=lambda x: -x[1])
        winner_key, _ = claims[0]
        canonical[winner_key] = code
        for loser_key, _ in claims[1:]:
            displaced.append(loser_key)

    # Assign synthetic codes to displaced + uncoded persons.
    # Displaced get JKT-X{nnn} so audit history is obvious.
    seq = 1
    for key in displaced:
        if key in canonical:
            continue
        canonical[key] = f"JKT-X{seq:03d}"
        seq += 1

    # Uncoded persons (e.g. Anurag) get the next free numeric JKT slot.
    next_numeric = 16
    used = {c for c in canonical.values() if re.match(r"^JKT\d+$", c)}
    # Also reserve any numeric codes that were already canonical for
    # other people (impossible loop but cheap to check).
    for key in people:
        if key not in canonical:
            while f"JKT{next_numeric:03d}" in used:
                next_numeric += 1
            code = f"JKT{next_numeric:03d}"
            canonical[key] = code
            used.add(code)
            next_numeric += 1

    return canonical


# ── DB-side helpers ──────────────────────────────────────────────────
def _split_name(name: str, fallback_code: str) -> tuple[str, str]:
    parts = name.split(maxsplit=1) if name else [fallback_code, ""]
    first = (parts[0] or fallback_code)[:64]
    last = (parts[1] if len(parts) > 1 else "")[:64]
    return first, last


async def _ensure_employee(
    db: AsyncSession,
    *,
    code: str,
    name: str,
    doj: Optional[date],
    permanent_cat_id: int,
    default_template_id: int,
) -> tuple[Employee, bool]:
    """Returns (emp, was_existing)."""
    existing = (
        await db.execute(select(Employee).where(Employee.employee_code == code))
    ).scalar_one_or_none()
    if existing is not None:
        if name:
            first, last = _split_name(name, code)
            existing.first_name = first
            existing.last_name = last
        if doj:
            existing.date_of_joining = doj
        return existing, True

    first, last = _split_name(name, code)
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
    return emp, False


async def _delete_demo_employees(db: AsyncSession) -> list[str]:
    """Drop the placeholder JKT014..JKT018 employees that older seed runs
    may have created. The User accounts behind them are kept so the
    test logins still work. The seed below recreates JKT014/JKT015 with
    the *real* spreadsheet employees (Pooja Kumawat, Atharv Sachin).

    Trainer profiles linked to the demo employees are *detached* (their
    `employee_id` is set to NULL) instead of cascading away — that
    avoids the FK chain `employees → trainer_profiles → trainer_sessions
    (RESTRICT)` blocking the delete when training sessions exist.
    """
    from sqlalchemy import update

    rows = (
        await db.execute(
            select(Employee).where(Employee.employee_code.in_(_DEMO_EMPLOYEE_CODES))
        )
    ).scalars().all()
    deleted: list[str] = []
    if not rows:
        return deleted

    demo_ids = [e.id for e in rows]

    # Lazy-import so the script runs even on environments where the
    # trainer module isn't loaded eagerly.
    try:
        from app.models import TrainerProfile

        await db.execute(
            update(TrainerProfile)
            .where(TrainerProfile.employee_id.in_(demo_ids))
            .values(employee_id=None)
        )
    except ImportError:
        pass

    for emp in rows:
        deleted.append(emp.employee_code)
        await db.delete(emp)
    return deleted


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
        # Don't overwrite admin-edited / GPS-punched real rows.
        if existing.source in ("import", "manual"):
            existing.status = status_
            existing.source = "import"


async def _resign(
    db: AsyncSession,
    *,
    emp: Employee,
    exit_date: date,
    reason: str,
) -> None:
    if emp.status != "resigned":
        emp.status = "resigned"
    emp.exit_date = exit_date

    existing = (
        await db.execute(
            select(Resignation).where(Resignation.employee_id == emp.id)
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Resignation(
                employee_id=emp.id,
                requested_at=datetime.combine(exit_date, datetime.min.time()),
                proposed_last_working_day=exit_date,
                actual_last_working_day=exit_date,
                reason=reason,
                status="cleared",
                notice_period_days=0,
                hr_cleared_at=datetime.utcnow(),
            )
        )
    else:
        existing.actual_last_working_day = exit_date
        existing.proposed_last_working_day = exit_date
        existing.status = "cleared"
        if not existing.hr_cleared_at:
            existing.hr_cleared_at = datetime.utcnow()
        if not existing.reason:
            existing.reason = reason


# ── Main flow ────────────────────────────────────────────────────────
async def main(*, gap_days: int, dry_run: bool, path: Path) -> None:
    if not path.exists():
        print(f"!! Workbook not found at {path}", file=sys.stderr)
        sys.exit(2)

    print(f"→ Reading {path}")
    wb_data = read_workbook(path)
    people = wb_data["people"]
    markers = wb_data["markers"]
    print(
        f"  Workbook: {len(people)} distinct persons, "
        f"{len(markers)} day markers."
    )

    canonical = resolve_canonical_codes(people)
    # Sanity: print the resolved code for each person.
    print("  Code resolution:")
    for key, info in sorted(people.items(), key=lambda kv: canonical[kv[0]]):
        c = canonical[key]
        doj = str(info["doj"]) if info["doj"] else "—"
        doe = str(info["doe"]) if info["doe"] else "—"
        print(
            f"    {c:9s} {info['name']:30s} DOJ={doj:12s} DOE={doe:12s}"
        )

    async with AsyncSessionLocal() as db:
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

        # 1. Cleanup leftover demo Employee rows. Flush immediately so
        #    the DELETE lands in the DB before the next pass tries to
        #    INSERT new employees that reuse the same codes (the
        #    spreadsheet's real JKT014 Pooja, JKT015 Atharv, JKT016
        #    Anurag would otherwise collide on the unique-code index
        #    when SQLAlchemy batches the writes).
        deleted = await _delete_demo_employees(db)
        await db.flush()
        if deleted:
            print(
                "  Removed demo employees (User logins preserved): "
                f"{', '.join(sorted(deleted))}"
            )

        # 2. Upsert each person.
        emp_by_key: dict[str, Employee] = {}
        created = 0
        updated = 0
        for key, info in people.items():
            code = canonical[key]
            emp, existed = await _ensure_employee(
                db,
                code=code,
                name=info["name"],
                doj=info["doj"],
                permanent_cat_id=permanent_cat.id,
                default_template_id=default_template.id,
            )
            await db.flush()
            emp_by_key[key] = emp
            if existed:
                updated += 1
            else:
                created += 1
        print(f"  Employees: {created} new, {updated} updated.")

        # 3. Import attendance markers.
        last_present_per_person: dict[str, date] = {}
        upserted = 0
        for key, year, month, day_n, marker in markers:
            emp = emp_by_key.get(key)
            if emp is None:
                continue
            try:
                d = date(year, month, day_n)
            except ValueError:
                continue
            if marker == "P":
                await _upsert_attendance(
                    db, employee_id=emp.id, on=d, status_="present"
                )
                upserted += 1
                if key not in last_present_per_person or d > last_present_per_person[key]:
                    last_present_per_person[key] = d
            elif marker == "L":
                await _upsert_attendance(
                    db, employee_id=emp.id, on=d, status_="leave"
                )
                upserted += 1
            # H markers are picked up from the Holiday table.
        print(f"  Attendance: {upserted} rows upserted from P/L markers.")

        # 4. Resignation pass.
        today = date.today()
        resigned_log = []
        for key, info in people.items():
            emp = emp_by_key[key]
            doe = info["doe"]
            lp = last_present_per_person.get(key)
            if doe:
                await _resign(
                    db,
                    emp=emp,
                    exit_date=doe,
                    reason=(
                        f"Auto-derived from attendance import — "
                        f"DOE {doe.isoformat()} per spreadsheet."
                    ),
                )
                resigned_log.append((emp.employee_code, info["name"], doe, "DOE"))
                continue
            if lp is not None and (today - lp).days >= gap_days:
                await _resign(
                    db,
                    emp=emp,
                    exit_date=lp,
                    reason=(
                        f"Auto-derived from attendance import — "
                        f"no presence after {lp.isoformat()}."
                    ),
                )
                resigned_log.append((emp.employee_code, info["name"], lp, "GAP"))

        if resigned_log:
            print("  Resignations:")
            for code, nm, ex, src in resigned_log:
                print(f"    · {code:9s} {nm:30s} exit={ex} source={src}")
        else:
            print("  No resignations triggered.")

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

"""Leave-year helpers.

Jaikalki runs the leave year on the Indian financial year:
**1 April → 31 March**. A balance row's `year` column stores the FY
*start* year, so FY 2025 means 1 Apr 2025 → 31 Mar 2026.
"""
from __future__ import annotations

from datetime import date

FY_START_MONTH = 4  # April


def financial_year_start(d: date) -> int:
    """Return the FY start year for a date.

    Jan–Mar belongs to the previous April's year:
        2026-02-10 → 2025   (FY 2025 = Apr'25–Mar'26)
        2025-04-01 → 2025
        2025-12-31 → 2025
    """
    return d.year if d.month >= FY_START_MONTH else d.year - 1


def financial_year_range(fy_start: int) -> tuple[date, date]:
    """(first_day, last_day) for a FY start year.

        2025 → (2025-04-01, 2026-03-31)
    """
    return date(fy_start, FY_START_MONTH, 1), date(
        fy_start + 1, FY_START_MONTH, 1
    ) - _one_day()


def _one_day():
    from datetime import timedelta

    return timedelta(days=1)

"""Registry of mobile-app modules.

Each `MODULE_KEYS` entry corresponds to one tile in the mobile More menu
(the `_MoreItem.label` keys mirror these exactly). Departments may
whitelist a subset of these keys via Department.enabled_modules; when
the field is NULL we treat it as "all modules visible".

Modules in `ALWAYS_ON` are not gateable — they're core profile / auth /
notifications surfaces that every employee always needs."""
from __future__ import annotations

from typing import Iterable, List, Optional


# Canonical key set — must match the strings used in
# hrms_mobile/lib/features/more/more_menu_page.dart `_MoreItem.key`.
MODULE_KEYS: list[str] = [
    "attendance",
    "leaves",
    "dwp",
    "approvals",
    "leave_approvals",
    "field_plan",
    "live_team_map",
    "sales_pipeline",
    "sales_targets",
    "my_leads",
    "verifications",
    "visitors",
    "book_room",
    "my_assets",
    "lms",
    "badges",
    "exams",
    "certificates",
    "trainers",
    "sessions",
    "my_goals",
    "feedback_360",
    "director_dashboard",
    "employees",
    "internal_jobs",
    "resignation",
    "justice",
    "payroll",
    "intern_expenses",
]

# Always-on modules — visible regardless of department mapping.
ALWAYS_ON: set[str] = {
    "notifications",
    "settings",
    "mfa_setup",
    # Reporting managers' view of leaving team members (asset NOC); the
    # app shows it only to people who manage a team.
    "team_exits",
}


def normalize(keys: Iterable[str] | None) -> list[str]:
    """Drop unknown keys and de-dupe while preserving registry order."""
    if keys is None:
        return []
    allowed = set(MODULE_KEYS)
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        k = (k or "").strip()
        if k in allowed and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def effective_modules(
    enabled_modules: Optional[list[str]],
) -> list[str]:
    """Return the merged set of modules a department member can see.

    - `None` → every module + always-on (default for departments without
      a custom mapping).
    - `[]` → only the always-on bundle.
    - explicit list → that list ∪ always-on.
    """
    if enabled_modules is None:
        return MODULE_KEYS + sorted(ALWAYS_ON)
    return normalize(enabled_modules) + sorted(ALWAYS_ON)

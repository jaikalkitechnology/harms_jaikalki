"""IST-aware JSON response.

The backend stores everything as naive UTC (datetime.utcnow()), which
keeps Celery scheduling, audit timestamps, and cross-region semantics
correct. But every API consumer in our stack is in India, so we
transform datetime values to Asia/Kolkata at the wire so callers see
"04:25 pm IST" without each having to convert.

How: subclass JSONResponse and walk the rendered dict, rewriting every
string that looks like an ISO datetime. Naive strings are assumed to
be UTC (which they are — see app.services.audit_service._now() etc.);
TZ-aware strings are honoured in place. Date-only strings
(YYYY-MM-DD) are left alone — those are calendar dates, not instants.

Wired at app startup via `FastAPI(default_response_class=ISTJSONResponse)`.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi.responses import JSONResponse

IST = ZoneInfo("Asia/Kolkata")

# Match an ISO 8601 datetime — the `T` separator and seconds are mandatory,
# microseconds and TZ suffix are optional. Date-only (no T) is excluded
# on purpose so calendar dates stay as `YYYY-MM-DD`.
_ISO_DT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)


def _shift_iso_string(s: str) -> str:
    if not _ISO_DT_RE.match(s):
        return s
    try:
        # `fromisoformat` accepts +HH:MM and the trailing Z (Python 3.11+).
        # For older Pythons, normalise Z first.
        raw = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return s
    if dt.tzinfo is None:
        # Bare ISO from naive UTC sources — tag it as UTC.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()


def _walk(obj: Any) -> Any:
    if isinstance(obj, dict):
        # Mutate in place to avoid building a copy on every response.
        for k, v in obj.items():
            obj[k] = _walk(v)
        return obj
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = _walk(v)
        return obj
    if isinstance(obj, str):
        return _shift_iso_string(obj)
    return obj


class ISTJSONResponse(JSONResponse):
    """JSONResponse that serialises every datetime field in IST."""

    def render(self, content: Any) -> bytes:
        # FastAPI runs `jsonable_encoder(content)` before render() is
        # called when content comes from a Pydantic model, which converts
        # datetimes to bare ISO strings. For raw dicts/lists returned by
        # endpoints, encode them ourselves through the same path.
        if isinstance(content, (dict, list)):
            content = _walk(content)
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

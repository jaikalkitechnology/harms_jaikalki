"""Letter numbers — ``JKT/HR/<code>/<seq>/<year>``, e.g. JKT/HR/AP/007/2026.

One sequence per letter code and year, shared by letters issued from
templates (employee_letters) and the payroll offer / confirmation flow
(generated_documents), so the two never hand out the same number.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmployeeLetter, GeneratedDocument

PREFIX = "JKT/HR"

# Letter type → code in the number. Offer (AL) and confirmation (CL)
# match the payroll flow's existing numbers. RV / TR stay clear of the
# RL / TL numbers on resignation and termination letters.
LETTER_CODES: dict[str, str] = {
    "offer": "AL",
    "appointment": "AP",
    "confirmation": "CL",
    "increment": "IN",
    "promotion": "PR",
    "experience": "EX",
    "relieving": "RV",
    "termination": "TR",
    "warning": "WN",
    "other": "GL",
}


async def next_letter_number(db: AsyncSession, letter_type: str, year: int) -> str:
    code = LETTER_CODES.get(letter_type, LETTER_CODES["other"])
    head = f"{PREFIX}/{code}/"
    tail = f"/{year}"
    numbers = [
        *(
            await db.execute(
                select(EmployeeLetter.letter_number).where(
                    EmployeeLetter.letter_number.like(f"{head}%{tail}")
                )
            )
        ).scalars(),
        *(
            await db.execute(
                select(GeneratedDocument.letter_number).where(
                    GeneratedDocument.letter_number.like(f"{head}%{tail}")
                )
            )
        ).scalars(),
    ]
    seq = 0
    for n in numbers:
        middle = (n or "")[len(head):-len(tail)]
        if middle.isdigit():
            seq = max(seq, int(middle))
    return f"{head}{seq + 1:03d}{tail}"

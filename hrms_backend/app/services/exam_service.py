"""Exam service: question bank, exam engine, auto-grading, certificates."""
from __future__ import annotations

import random
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import (
    AttemptAnswer,
    Certificate,
    Course,
    Employee,
    Exam,
    ExamAttempt,
    ExamQuestion,
    QuestionBank,
    QuestionOption,
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _today() -> date:
    return _now().date()


# ── Question bank ────────────────────────────────────────────────────
async def create_question(
    db: AsyncSession, *, payload: dict
) -> QuestionBank:
    options_data = payload.pop("options", [])
    if payload["question_type"] in ("single_choice", "multiple_choice", "true_false"):
        if not options_data:
            raise ValidationError("Choice questions require options")
        if not any(o.get("is_correct") for o in (
            o.model_dump() if hasattr(o, "model_dump") else o
            for o in options_data
        )):
            raise ValidationError("At least one option must be marked correct")

    question = QuestionBank(**payload)
    db.add(question)
    await db.flush()
    for spec in options_data:
        d = spec.model_dump() if hasattr(spec, "model_dump") else dict(spec)
        db.add(QuestionOption(question_id=question.id, **d))
    await db.commit()
    await db.refresh(question)
    return question


async def list_questions(
    db: AsyncSession,
    *,
    department_id: Optional[int] = None,
    course_id: Optional[int] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = "active",
    limit: int = 500,
) -> Sequence[QuestionBank]:
    stmt = select(QuestionBank)
    if status:
        stmt = stmt.where(QuestionBank.status == status)
    if department_id is not None:
        stmt = stmt.where(QuestionBank.department_id == department_id)
    if course_id is not None:
        stmt = stmt.where(QuestionBank.course_id == course_id)
    if topic:
        stmt = stmt.where(QuestionBank.topic == topic)
    if difficulty:
        stmt = stmt.where(QuestionBank.difficulty == difficulty)
    stmt = stmt.order_by(QuestionBank.created_at.desc()).limit(limit)
    try:
        return (await db.execute(stmt)).scalars().all()
    except Exception:
        # Fallback for un-migrated DB where exam_questions.course_id
        # doesn't exist yet — drop the course filter and try again so
        # the question bank UI still loads while operators run the
        # column sync.
        await db.rollback()
        if course_id is None:
            raise
        from sqlalchemy.exc import OperationalError
        # Retry without the course filter
        stmt2 = select(QuestionBank)
        if status:
            stmt2 = stmt2.where(QuestionBank.status == status)
        if department_id is not None:
            stmt2 = stmt2.where(QuestionBank.department_id == department_id)
        if topic:
            stmt2 = stmt2.where(QuestionBank.topic == topic)
        if difficulty:
            stmt2 = stmt2.where(QuestionBank.difficulty == difficulty)
        stmt2 = stmt2.order_by(QuestionBank.created_at.desc()).limit(limit)
        try:
            return (await db.execute(stmt2)).scalars().all()
        except OperationalError:
            await db.rollback()
            return []


async def set_exam_questions(
    db: AsyncSession, exam_id: int, *, question_ids: list[int]
) -> "Exam":
    """Replace the full set of questions on an exam, idempotently.

    Removes anything not in the new list, adds anything missing,
    preserves existing rows that overlap (so created_at on the join
    rows isn't churned)."""
    from app.models import Exam, ExamQuestion

    exam = (
        await db.execute(select(Exam).where(Exam.id == exam_id))
    ).scalar_one_or_none()
    if not exam:
        raise NotFoundError("Exam not found")

    existing_rows = (
        await db.execute(
            select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
        )
    ).scalars().all()
    existing_ids = {r.question_id for r in existing_rows}
    target_ids = set(question_ids)

    # Remove
    for r in existing_rows:
        if r.question_id not in target_ids:
            await db.delete(r)
    # Add
    for q_id in target_ids - existing_ids:
        db.add(ExamQuestion(exam_id=exam_id, question_id=q_id))

    # Keep total_questions consistent with the actual selection
    exam.total_questions = len(target_ids) or exam.total_questions
    await db.commit()
    await db.refresh(exam)
    return exam


# ── Exam config ──────────────────────────────────────────────────────
async def create_exam(db: AsyncSession, *, payload: dict) -> Exam:
    if (
        await db.execute(select(Exam).where(Exam.code == payload["code"]))
    ).scalar_one_or_none():
        raise ConflictError(f"Exam '{payload['code']}' already exists")
    question_ids = payload.pop("question_ids", [])
    exam = Exam(**payload, is_published=False)
    db.add(exam)
    await db.flush()
    for i, qid in enumerate(question_ids):
        q = (
            await db.execute(
                select(QuestionBank).where(QuestionBank.id == qid)
            )
        ).scalar_one_or_none()
        if not q:
            raise NotFoundError(f"Question id {qid} not found")
        db.add(ExamQuestion(exam_id=exam.id, question_id=qid, sort_order=i))
    await db.commit()
    await db.refresh(exam)
    return exam


async def get_exam(db: AsyncSession, exam_id: int) -> Exam:
    exam = (
        await db.execute(select(Exam).where(Exam.id == exam_id))
    ).scalar_one_or_none()
    if not exam:
        raise NotFoundError("Exam not found")
    return exam


async def publish_exam(
    db: AsyncSession, exam_id: int, *, is_published: bool
) -> Exam:
    exam = await get_exam(db, exam_id)
    if is_published and not exam.questions:
        raise ValidationError("Cannot publish an exam without questions")
    exam.is_published = is_published
    await db.commit()
    await db.refresh(exam)
    return exam


async def list_exams(
    db: AsyncSession,
    *,
    course_id: Optional[int] = None,
    exam_type: Optional[str] = None,
    published_only: bool = True,
) -> Sequence[Exam]:
    stmt = select(Exam)
    if published_only:
        stmt = stmt.where(Exam.is_published.is_(True))
    if course_id is not None:
        stmt = stmt.where(Exam.course_id == course_id)
    if exam_type:
        stmt = stmt.where(Exam.exam_type == exam_type)
    stmt = stmt.order_by(Exam.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


# ── Attempts ─────────────────────────────────────────────────────────
async def _attempts_for(
    db: AsyncSession, *, exam_id: int, employee_id: int
) -> list[ExamAttempt]:
    rows = (
        await db.execute(
            select(ExamAttempt)
            .where(ExamAttempt.exam_id == exam_id)
            .where(ExamAttempt.employee_id == employee_id)
            .order_by(ExamAttempt.started_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def start_attempt(
    db: AsyncSession,
    *,
    exam: Exam,
    employee: Employee,
    ip_address: Optional[str] = None,
    device_info: Optional[str] = None,
) -> tuple[ExamAttempt, list[QuestionBank]]:
    if not exam.is_published:
        raise ValidationError("Exam is not published")

    prior = await _attempts_for(
        db, exam_id=exam.id, employee_id=employee.id
    )
    in_progress = [a for a in prior if a.status == "in_progress"]
    if in_progress:
        # Resume existing
        attempt = in_progress[0]
        questions = await _questions_for_attempt(db, attempt)
        return attempt, questions

    finished = [
        a
        for a in prior
        if a.status in ("submitted", "auto_submitted")
    ]
    if len(finished) >= exam.attempts_allowed:
        raise ValidationError(
            f"You've used all {exam.attempts_allowed} attempts"
        )
    if exam.cooldown_hours and finished:
        last = finished[0]
        if last.submitted_at:
            elapsed = (_now() - last.submitted_at).total_seconds() / 3600
            if elapsed < exam.cooldown_hours:
                hours_left = round(exam.cooldown_hours - elapsed, 1)
                raise ValidationError(
                    f"Cooldown active — try again in {hours_left}h"
                )

    pool = [eq.question_id for eq in exam.questions]
    if exam.question_selection == "random":
        random.shuffle(pool)
        pool = pool[: exam.total_questions]
    elif exam.shuffle_questions:
        random.shuffle(pool)
    if not pool:
        raise ValidationError("Exam has no questions")

    attempt = ExamAttempt(
        exam_id=exam.id,
        employee_id=employee.id,
        started_at=_now(),
        status="in_progress",
        attempt_number=len(finished) + 1,
        ip_address=ip_address,
        device_info=device_info,
        question_order=pool,
        cheating_flags=[],
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    questions = await _questions_for_attempt(db, attempt)
    return attempt, questions


async def _questions_for_attempt(
    db: AsyncSession, attempt: ExamAttempt
) -> list[QuestionBank]:
    ids = attempt.question_order or []
    if not ids:
        return []
    rows = (
        await db.execute(
            select(QuestionBank).where(QuestionBank.id.in_(ids))
        )
    ).scalars().all()
    by_id = {q.id: q for q in rows}
    return [by_id[i] for i in ids if i in by_id]


async def get_attempt(
    db: AsyncSession, attempt_id: int
) -> ExamAttempt:
    a = (
        await db.execute(
            select(ExamAttempt).where(ExamAttempt.id == attempt_id)
        )
    ).scalar_one_or_none()
    if not a:
        raise NotFoundError("Attempt not found")
    return a


async def submit_attempt(
    db: AsyncSession,
    *,
    attempt: ExamAttempt,
    employee: Employee,
    answers: list[dict],
    cheating_flags: Optional[list[dict]] = None,
    auto_submit: bool = False,
) -> ExamAttempt:
    if attempt.employee_id != employee.id:
        raise ForbiddenError("Not your attempt")
    if attempt.status != "in_progress":
        raise ValidationError(f"Attempt already {attempt.status}")

    exam = await get_exam(db, attempt.exam_id)
    questions = (
        await db.execute(
            select(QuestionBank).where(
                QuestionBank.id.in_(attempt.question_order or [])
            )
        )
    ).scalars().all()
    by_id = {q.id: q for q in questions}

    total_score = 0
    max_score = sum(q.marks for q in questions)
    answered_qids = set()
    for ans in answers:
        qid = ans["question_id"]
        if qid not in by_id or qid in answered_qids:
            continue
        answered_qids.add(qid)
        q = by_id[qid]
        selected = ans.get("selected_option_ids") or []
        text_answer = ans.get("text_answer")
        time_taken = ans.get("time_taken_seconds", 0)

        is_correct = False
        if q.question_type in ("single_choice", "true_false"):
            correct_ids = {o.id for o in q.options if o.is_correct}
            is_correct = (
                len(selected) == 1 and selected[0] in correct_ids
            )
        elif q.question_type == "multiple_choice":
            correct_ids = {o.id for o in q.options if o.is_correct}
            is_correct = set(selected) == correct_ids and bool(selected)
        elif q.question_type == "fill_blank":
            correct_texts = {
                o.option_text.strip().lower()
                for o in q.options
                if o.is_correct
            }
            if text_answer:
                is_correct = text_answer.strip().lower() in correct_texts
        # short_answer / match_pairs: scored by reviewer manually (default false)

        marks = q.marks if is_correct else 0
        if not is_correct and exam.negative_marking and (selected or text_answer):
            marks = -max(1, q.marks // 4)
        total_score += marks

        db.add(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=qid,
                selected_option_ids=selected or None,
                text_answer=text_answer,
                is_correct=is_correct,
                marks_awarded=marks,
                time_taken_seconds=time_taken,
            )
        )

    attempt.total_score = max(0, total_score)
    attempt.max_score = max_score
    attempt.percentage = (
        Decimal(attempt.total_score) / Decimal(max_score) * Decimal("100")
        if max_score > 0
        else Decimal("0")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    attempt.passed = bool(
        attempt.percentage >= Decimal(exam.passing_percentage)
    )
    attempt.submitted_at = _now()
    attempt.time_taken_seconds = int(
        (attempt.submitted_at - attempt.started_at).total_seconds()
    )
    if cheating_flags:
        existing = list(attempt.cheating_flags or [])
        existing.extend(cheating_flags)
        attempt.cheating_flags = existing
    attempt.status = "auto_submitted" if auto_submit else "submitted"

    await db.commit()
    await db.refresh(attempt)

    # Issue certificate for passed certification exams
    if attempt.passed and exam.exam_type in ("certification", "mandatory"):
        await issue_certificate(
            db, attempt=attempt, exam=exam, employee=employee
        )

    return attempt


async def add_cheating_flag(
    db: AsyncSession,
    *,
    attempt: ExamAttempt,
    employee: Employee,
    flag_type: str,
    note: Optional[str] = None,
) -> ExamAttempt:
    if attempt.employee_id != employee.id:
        raise ForbiddenError("Not your attempt")
    flags = list(attempt.cheating_flags or [])
    flags.append(
        {
            "type": flag_type,
            "at": _now().isoformat(),
            "note": note,
        }
    )
    attempt.cheating_flags = flags
    # If too many flags, invalidate the attempt
    if len([f for f in flags if f["type"] != "other"]) >= 5:
        attempt.status = "invalidated"
    await db.commit()
    await db.refresh(attempt)
    return attempt


async def list_my_attempts(
    db: AsyncSession, employee_id: int
) -> Sequence[ExamAttempt]:
    return (
        await db.execute(
            select(ExamAttempt)
            .where(ExamAttempt.employee_id == employee_id)
            .order_by(ExamAttempt.started_at.desc())
        )
    ).scalars().all()


# ── Certificates ────────────────────────────────────────────────────
def _new_certificate_number() -> str:
    year = _now().year
    return f"JKT/CERT/{year}/{secrets.token_hex(4).upper()}"


async def issue_certificate(
    db: AsyncSession,
    *,
    attempt: ExamAttempt,
    exam: Exam,
    employee: Employee,
) -> Certificate:
    issued = _today()
    expiry: Optional[date] = None
    if exam.validity_months:
        expiry = issued + timedelta(days=30 * exam.validity_months)

    cert = Certificate(
        certificate_number=_new_certificate_number(),
        employee_id=employee.id,
        course_id=exam.course_id,
        exam_attempt_id=attempt.id,
        title=exam.title,
        issued_date=issued,
        expiry_date=expiry,
        score_percentage=attempt.percentage,
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert


async def list_my_certificates(
    db: AsyncSession, employee_id: int
) -> Sequence[Certificate]:
    return (
        await db.execute(
            select(Certificate)
            .where(Certificate.employee_id == employee_id)
            .order_by(Certificate.issued_date.desc())
        )
    ).scalars().all()


# Admin CRUD for certificates
async def list_certificates(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    course_id: Optional[int] = None,
    is_revoked: Optional[bool] = None,
    search: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 200,
    offset: int = 0,
) -> Sequence[Certificate]:
    from sqlalchemy import or_

    stmt = select(Certificate)
    if employee_id is not None:
        stmt = stmt.where(Certificate.employee_id == employee_id)
    if course_id is not None:
        stmt = stmt.where(Certificate.course_id == course_id)
    if is_revoked is not None:
        stmt = stmt.where(Certificate.is_revoked == is_revoked)
    if from_date is not None:
        stmt = stmt.where(Certificate.issued_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(Certificate.issued_date <= to_date)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Certificate.certificate_number.ilike(like),
                Certificate.title.ilike(like),
            )
        )
    stmt = (
        stmt.order_by(Certificate.issued_date.desc(), Certificate.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await db.execute(stmt)).scalars().all()


async def admin_issue_certificate(
    db: AsyncSession, *, payload: dict
) -> Certificate:
    """Admin-driven certificate issuance (no exam attempt required)."""
    emp = (
        await db.execute(
            select(Employee).where(Employee.id == payload["employee_id"])
        )
    ).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")

    cert = Certificate(
        certificate_number=_new_certificate_number(),
        employee_id=emp.id,
        course_id=payload.get("course_id"),
        exam_attempt_id=payload.get("exam_attempt_id"),
        title=payload["title"],
        certificate_type=payload.get("certificate_type") or "achievement",
        body_text=payload.get("body_text"),
        issued_date=payload.get("issued_date") or _today(),
        expiry_date=payload.get("expiry_date"),
        score_percentage=payload.get("score_percentage"),
        file_key=payload.get("file_key"),
        file_name=payload.get("file_name"),
        mime_type=payload.get("mime_type"),
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert


async def update_certificate(
    db: AsyncSession, certificate_id: int, *, payload: dict
) -> Certificate:
    cert = await get_certificate(db, certificate_id)
    allowed = {
        "title",
        "certificate_type",
        "body_text",
        "issued_date",
        "expiry_date",
        "score_percentage",
        "course_id",
    }
    # Allow body_text to be cleared by passing "" — distinguish from None
    # (which means "field omitted from update").
    for k, v in payload.items():
        if k not in allowed:
            continue
        if k == "body_text":
            cert.body_text = v if v else None
            continue
        if v is None:
            continue
        setattr(cert, k, v)
    await db.commit()
    await db.refresh(cert)
    return cert


async def revoke_certificate(
    db: AsyncSession, certificate_id: int, *, reason: str
) -> Certificate:
    cert = await get_certificate(db, certificate_id)
    cert.is_revoked = True
    cert.revoked_reason = reason
    await db.commit()
    await db.refresh(cert)
    return cert


async def restore_certificate(
    db: AsyncSession, certificate_id: int
) -> Certificate:
    cert = await get_certificate(db, certificate_id)
    cert.is_revoked = False
    cert.revoked_reason = None
    await db.commit()
    await db.refresh(cert)
    return cert


async def verify_certificate(
    db: AsyncSession, certificate_number: str
) -> dict:
    cert = (
        await db.execute(
            select(Certificate).where(
                Certificate.certificate_number == certificate_number
            )
        )
    ).scalar_one_or_none()
    if not cert:
        return {"valid": False, "certificate_number": certificate_number}

    employee = (
        await db.execute(
            select(Employee).where(Employee.id == cert.employee_id)
        )
    ).scalar_one_or_none()
    today = _today()
    valid = not cert.is_revoked and (
        cert.expiry_date is None or cert.expiry_date >= today
    )
    return {
        "valid": valid,
        "certificate_number": cert.certificate_number,
        "employee_name": (
            f"{employee.first_name} {employee.last_name}".strip()
            if employee
            else None
        ),
        "title": cert.title,
        "issued_date": cert.issued_date,
        "expiry_date": cert.expiry_date,
        "score_percentage": cert.score_percentage,
        "is_revoked": cert.is_revoked,
        "revoked_reason": cert.revoked_reason,
    }


async def get_certificate(
    db: AsyncSession, certificate_id: int
) -> Certificate:
    c = (
        await db.execute(
            select(Certificate).where(Certificate.id == certificate_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise NotFoundError("Certificate not found")
    return c


# ── Mutations: question + exam update / delete ────────────────────────
async def update_question(
    db: AsyncSession, question_id: int, *, payload: dict
) -> "QuestionBank":
    from app.models import QuestionBank
    q = (
        await db.execute(select(QuestionBank).where(QuestionBank.id == question_id))
    ).scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found")
    allowed = {
        "question_text", "question_type", "department_id", "topic",
        "difficulty", "language", "marks", "time_seconds", "explanation",
        "status",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(q, k, v)
    await db.commit()
    await db.refresh(q)
    return q


async def delete_question(db: AsyncSession, question_id: int) -> None:
    from app.models import QuestionBank
    q = (
        await db.execute(select(QuestionBank).where(QuestionBank.id == question_id))
    ).scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found")
    await db.delete(q)
    await db.commit()


async def update_exam(db: AsyncSession, exam_id: int, *, payload: dict) -> "Exam":
    from app.models import Exam
    exam = (
        await db.execute(select(Exam).where(Exam.id == exam_id))
    ).scalar_one_or_none()
    if not exam:
        raise NotFoundError("Exam not found")
    allowed = {
        "title", "description", "course_id", "department_id", "exam_type",
        "total_questions", "time_limit_minutes", "passing_percentage",
        "shuffle_questions", "shuffle_options", "attempts_allowed",
        "cooldown_hours", "negative_marking", "validity_months",
    }
    for k, v in payload.items():
        if k in allowed and v is not None:
            setattr(exam, k, v)
    await db.commit()
    await db.refresh(exam)
    return exam


async def delete_exam(db: AsyncSession, exam_id: int) -> None:
    from app.models import Exam
    exam = (
        await db.execute(select(Exam).where(Exam.id == exam_id))
    ).scalar_one_or_none()
    if not exam:
        raise NotFoundError("Exam not found")
    await db.delete(exam)
    await db.commit()


async def replace_question_options(
    db: AsyncSession, question_id: int, *, options: list[dict]
) -> "QuestionBank":
    """Replace the full set of options on a question. Used when an
    admin edits a saved question's choices (which row is correct,
    a typo in the option text, etc.)."""
    from app.models import QuestionBank, QuestionOption

    q = (
        await db.execute(select(QuestionBank).where(QuestionBank.id == question_id))
    ).scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found")

    # Wipe existing options and re-insert in the order received.
    for o in list(q.options or []):
        await db.delete(o)
    await db.flush()
    for i, opt in enumerate(options):
        db.add(
            QuestionOption(
                question_id=q.id,
                option_text=str(opt.get("option_text", "")),
                is_correct=bool(opt.get("is_correct", False)),
                sort_order=int(opt.get("sort_order", i)),
            )
        )
    await db.commit()
    await db.refresh(q)
    return q

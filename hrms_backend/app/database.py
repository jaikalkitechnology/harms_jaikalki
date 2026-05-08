from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_tables() -> None:
    """Create any tables that don't yet exist.

    For dev / first-boot convenience. Production should use Alembic
    migrations (`alembic upgrade head`) instead — this is enabled by
    `settings.AUTO_CREATE_TABLES`. `create_all()` only adds missing
    tables, it does NOT migrate columns/indexes on existing ones, so
    Alembic remains the source of truth.

    Importing `app.models` here ensures every model is registered with
    `Base.metadata` before we run create_all.
    """
    import app.models  # noqa: F401  — register all models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Columns that need to be added to *existing* tables — `create_all`
# only handles new tables, not new columns. Each entry is run
# idempotently at startup if AUTO_CREATE_TABLES is on.
#   (table, column, column_definition, optional_fk_constraint_target)
_PENDING_COLUMNS: list[tuple[str, str, str, str | None]] = [
    (
        "exam_questions",
        "course_id",
        "INT NULL",
        "lms_courses(id) ON DELETE SET NULL",
    ),
    ("sales_leads", "won_approval_status", "VARCHAR(16) NULL", None),
    ("sales_leads", "won_rejection_reason", "VARCHAR(500) NULL", None),
    ("sales_leads", "won_requested_at", "DATETIME NULL", None),
    ("sales_leads", "won_decided_at", "DATETIME NULL", None),
    ("sales_leads", "won_decided_by_user_id", "INT NULL", None),
    ("exam_certificates", "certificate_type", "VARCHAR(32) NULL", None),
    ("exam_certificates", "body_text", "VARCHAR(1000) NULL", None),
    (
        "job_postings",
        "published_to_app",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    ("report_saved", "file_url", "VARCHAR(500) NULL", None),
    ("report_saved", "file_name", "VARCHAR(255) NULL", None),
    ("report_saved", "file_size", "INT NULL", None),
    ("report_saved", "file_mime", "VARCHAR(120) NULL", None),
]


async def sync_columns() -> None:
    """Add any columns listed in _PENDING_COLUMNS that are missing
    from the live schema. Safe to call repeatedly; existing columns
    are skipped and FK constraint failures are swallowed.

    Logs each ALTER it runs (or skips), and re-raises with an
    actionable message if it can't apply a needed change so the
    operator sees something useful in journalctl."""
    import logging

    from sqlalchemy import text

    log = logging.getLogger(__name__)

    async with engine.begin() as conn:
        # Resolve the live database name once so log messages and the
        # actionable runbook on failure are fully qualified.
        dbname = (await conn.execute(text("SELECT DATABASE()"))).scalar() or ""
        qual = lambda t: f"{dbname}.{t}" if dbname else t  # noqa: E731

        for table, column, col_def, fk in _PENDING_COLUMNS:
            exists = (
                await conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() "
                        "AND TABLE_NAME = :t AND COLUMN_NAME = :c"
                    ),
                    {"t": table, "c": column},
                )
            ).scalar()
            if exists:
                log.info("sync_columns: %s.%s already present", qual(table), column)
                continue

            try:
                await conn.execute(
                    text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def}")
                )
                log.info("sync_columns: added %s.%s", qual(table), column)
            except Exception as e:
                log.error(
                    "sync_columns: FAILED to add %s.%s — %s. "
                    "Run this once as a privileged DB user:\n"
                    "  ALTER TABLE %s ADD COLUMN %s %s;",
                    qual(table), column, e, qual(table), column, col_def,
                )
                raise

            try:
                await conn.execute(
                    text(
                        f"CREATE INDEX `idx_{table}_{column}` "
                        f"ON `{table}` (`{column}`)"
                    )
                )
            except Exception as e:
                log.warning(
                    "sync_columns: index for %s.%s skipped — %s",
                    qual(table), column, e,
                )

            if fk:
                try:
                    await conn.execute(
                        text(
                            f"ALTER TABLE `{table}` "
                            f"ADD CONSTRAINT `fk_{table}_{column}` "
                            f"FOREIGN KEY (`{column}`) REFERENCES {fk}"
                        )
                    )
                except Exception as e:
                    log.warning(
                        "sync_columns: FK %s.%s -> %s skipped — %s",
                        qual(table), column, fk, e,
                    )

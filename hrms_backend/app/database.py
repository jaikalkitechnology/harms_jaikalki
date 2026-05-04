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
        "courses(id) ON DELETE SET NULL",
    ),
]


async def sync_columns() -> None:
    """Add any columns listed in _PENDING_COLUMNS that are missing
    from the live schema. Safe to call repeatedly; existing columns
    are skipped and FK constraint failures are swallowed (they happen
    when the constraint already exists or the dialect doesn't support
    it). Runs only when AUTO_CREATE_TABLES is enabled."""
    from sqlalchemy import text

    async with engine.begin() as conn:
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
                continue
            await conn.execute(
                text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def}")
            )
            await conn.execute(
                text(
                    f"CREATE INDEX `idx_{table}_{column}` "
                    f"ON `{table}` (`{column}`)"
                )
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
                except Exception:
                    pass  # FK may already exist or be unsupported

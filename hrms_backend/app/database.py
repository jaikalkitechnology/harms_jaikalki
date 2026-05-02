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

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.dependencies import get_db
from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def seeded(test_engine) -> None:
    """Run the auth seeder against the test DB once per test."""
    SessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    from scripts.seed_auth import (
        seed_departments,
        seed_permissions,
        seed_roles,
        seed_users,
    )

    async with SessionLocal() as db:
        perms = await seed_permissions(db)
        roles = await seed_roles(db, perms)
        await seed_departments(db)
        await seed_users(db, roles)
        await db.commit()


@pytest_asyncio.fixture
async def client(test_engine, seeded) -> AsyncGenerator[AsyncClient, None]:
    SessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _get_db_override() -> AsyncGenerator[AsyncSession, None]:
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)

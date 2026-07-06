"""
OpenS2P – Test Configuration
=============================
Async pytest fixtures for integration testing with a dedicated test database.

Usage:

    cd backend && pytest ../tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.session import get_session
from app.main import app
from app.models import Base
from app.security.password import hash_password

TEST_DATABASE_URL = "postgresql+asyncpg://opens2p:opens2p@localhost:5432/opens2p_test"


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for async fixtures."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create the test database and return an engine connected to it."""
    # Connect to default DB first to create test DB
    root_engine = create_async_engine(
        "postgresql+asyncpg://opens2p:opens2p@localhost:5432/opens2p_dev",
    )
    async with root_engine.connect() as conn:
        await conn.execute(text("COMMIT"))  # close open transaction
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'opens2p_test'"),
        )
        if not result.scalar():
            await conn.execute(text("CREATE DATABASE opens2p_test"))
    await root_engine.dispose()

    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean transactional session per test."""
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client with fresh session per request."""

    async def _get_session():
        factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as s:
            try:
                yield s
            finally:
                await s.close()

    app.dependency_overrides[get_session] = _get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_tenant(session: AsyncSession) -> uuid.UUID:
    """Insert a minimal tenant and return its ID."""
    tid = uuid.uuid4()
    await session.execute(
        text("INSERT INTO tenants (id, tenant_code, name, status) VALUES (:id, :code, :n, 'ACTIVE')"),
        {"id": tid, "code": "TEST", "n": "Test Tenant"},
    )
    await session.commit()
    return tid


@pytest_asyncio.fixture
async def seed_admin_user(session: AsyncSession, seed_tenant: uuid.UUID) -> uuid.UUID:
    """Insert an admin user and return the user ID."""
    uid = uuid.uuid4()
    await session.execute(
        text("""
            INSERT INTO users (id, tenant_id, username, email, hashed_password, is_superuser)
            VALUES (:id, :tid, 'admin', 'admin@test.com', :pwd, true)
        """),
        {"id": uid, "tid": seed_tenant, "pwd": hash_password("admin123")},
    )
    await session.commit()
    return uid

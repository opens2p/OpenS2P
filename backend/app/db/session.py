"""
OpenS2P – Database session management
=======================================
Async SQLAlchemy engine and session factory with tenant context support.

The engine is created lazily on first access so that the module can be
imported without the ``asyncpg`` driver being installed.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _resolve_db_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://opens2p:opens2p@localhost:5432/opens2p_dev",
    )
    # Convert sync URL to async if needed
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@lru_cache(maxsize=1)
def get_engine():
    """Return the singleton async engine (created lazily)."""
    return create_async_engine(
        _resolve_db_url(),
        echo=False,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def get_session_factory():
    """Return the singleton ``async_sessionmaker``."""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session and closes it on teardown."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """Context manager that commits on success, rolls back on error.

    Usage::

        async with transaction(session):
            repo = SomeRepository(session, tenant_id=...)
            await repo.create(data)
            # auto-committed here on success
    """
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise

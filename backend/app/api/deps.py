"""
OpenS2P – API Dependencies
===========================
FastAPI dependency-injection functions shared by all endpoints.
"""

from __future__ import annotations

import uuid
from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.security.dependencies import AuthContext, optional_auth, require_auth
from app.services.uow import UnitOfWork


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session."""
    async for session in get_session():
        yield session


async def get_tenant_id(
    x_tenant_id: str | None = Header(None),
    auth: AuthContext | None = Depends(optional_auth),
) -> uuid.UUID | None:
    """Resolve tenant ID — from the JWT if authenticated, else from header.

    Uses ``optional_auth`` so that unauthenticated endpoints (e.g. login)
    can still function without a token.
    """
    if auth is not None:
        return auth.tenant_id
    if x_tenant_id is None:
        return None
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-Id format",
        ) from exc


async def get_unit_of_work(
    session: AsyncSession = Depends(get_db_session),
    tenant_id: uuid.UUID | None = Depends(get_tenant_id),
) -> AsyncGenerator[UnitOfWork, None]:
    """Provide a UnitOfWork scoped to the request's tenant."""
    uow = UnitOfWork(session=session, tenant_id=tenant_id)
    yield uow

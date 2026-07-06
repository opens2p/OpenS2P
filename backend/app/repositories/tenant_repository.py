"""
OpenS2P – Tenant repository
============================
Tenant is the root aggregate — it has no ``tenant_id`` FK, so queries
are unscoped.  Every other repository depends on a resolved tenant.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Root tenant repository — no tenant scoping."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Tenant, tenant_id=None)

    async def get_by_code(self, tenant_code: str) -> Tenant | None:
        """Look up a tenant by its unique code."""
        stmt = select(Tenant).where(Tenant.tenant_code == tenant_code)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Tenant | None:
        """Look up a tenant by domain name."""
        stmt = select(Tenant).where(Tenant.domain == domain)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def create(self, data: dict[str, Any]) -> Tenant:
        """Create a tenant with a generated UUID if not provided."""
        if "id" not in data:
            data["id"] = uuid.uuid4()
        return await super().create(data)

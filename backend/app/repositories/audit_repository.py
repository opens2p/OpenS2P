"""
OpenS2P – Audit repository
===========================
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditEvent]):
    """Immutable audit-log repository — no tenant scoping by default
    (admins may search across tenants)."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID | None = None) -> None:
        super().__init__(session, AuditEvent, tenant_id=tenant_id)

    # ── logging ───────────────────────────────────────────────────────────

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        event_type: str,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditEvent:
        """Record an immutable audit entry."""
        event = AuditEvent(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            old_values=old_values,
            new_values=new_values,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        return await self.create(event)

    # ── queries ───────────────────────────────────────────────────────────

    async def list_by_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Full history for a specific business object."""
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == entity_type,
                AuditEvent.entity_id == entity_id,
            )
            .order_by(AuditEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if self.tenant_id is not None:
            stmt = stmt.where(AuditEvent.tenant_id == self.tenant_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_type(
        self,
        event_type: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """All events of a given type (e.g. ``SUPPLIER_UPDATED``)."""
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.event_type == event_type)
            .order_by(AuditEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if self.tenant_id is not None:
            stmt = stmt.where(AuditEvent.tenant_id == self.tenant_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_timeline(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Chronological audit feed for a tenant."""
        stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc())
        if self.tenant_id is not None:
            stmt = stmt.where(AuditEvent.tenant_id == self.tenant_id)
        if since is not None:
            stmt = stmt.where(AuditEvent.created_at >= since)
        if until is not None:
            stmt = stmt.where(AuditEvent.created_at <= until)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

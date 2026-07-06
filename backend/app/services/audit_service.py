"""
OpenS2P – Audit Service
========================
High-level API for recording and querying audit events.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.models import AuditEvent
from app.services.uow import UnitOfWork


class AuditService:
    """Audit trail operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def record(
        self,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        event_type: str,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Record an immutable audit event for the current tenant."""
        return await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            old_values=old_values,
            new_values=new_values,
            created_by=None,  # caller should set actor_id separately
        )

    async def get_history(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Full change history for a business object."""
        return await self.uow.audit.list_by_entity(
            entity_type, entity_id, skip=skip, limit=limit,
        )

    async def get_timeline(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Chronological feed of all audit events for the tenant."""
        return await self.uow.audit.list_timeline(
            since=since, until=until, skip=skip, limit=limit,
        )

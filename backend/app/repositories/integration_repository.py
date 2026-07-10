"""
Integration repositories.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.integration import IntegrationConnection, IntegrationRun, IntegrationLog, FieldMapping, ExternalReference
from app.repositories.base import BaseRepository


class IntegrationConnectionRepository(BaseRepository[IntegrationConnection]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, IntegrationConnection, tenant_id=tenant_id)

    async def get_by_type(self, connector_type: str) -> list[IntegrationConnection]:
        stmt = self._stmt().where(IntegrationConnection.connector_type == connector_type)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def mark_connected(self, connection_id: uuid.UUID) -> IntegrationConnection | None:
        return await self.update(connection_id, {"is_connected": True, "last_test_at": datetime.utcnow()})

    async def mark_disconnected(self, connection_id: uuid.UUID) -> IntegrationConnection | None:
        return await self.update(connection_id, {"is_connected": False})

    async def update_sync_time(self, connection_id: uuid.UUID) -> IntegrationConnection | None:
        return await self.update(connection_id, {"last_sync_at": datetime.utcnow()})


class IntegrationRunRepository(BaseRepository[IntegrationRun]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, IntegrationRun, tenant_id=tenant_id)

    async def list_by_connection(self, connection_id: uuid.UUID) -> list[IntegrationRun]:
        stmt = self._stmt().where(IntegrationRun.connection_id == connection_id).order_by(IntegrationRun.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())


class IntegrationLogRepository(BaseRepository[IntegrationLog]):
    """Note: IntegrationLog doesn't have tenant_id, uses run_id instead."""
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_run(self, run_id: uuid.UUID) -> list[IntegrationLog]:
        stmt = select(IntegrationLog).where(IntegrationLog.run_id == run_id).order_by(IntegrationLog.created_at)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def create(self, data: dict[str, Any]) -> IntegrationLog:
        instance = IntegrationLog(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

"""
Analytics repositories.
"""
from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analytics import KPIDefinition, KPISnapshot, DashboardConfig, SavedReport, ReportExecution
from app.repositories.base import BaseRepository


class KPIDefinitionRepository(BaseRepository[KPIDefinition]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, KPIDefinition, tenant_id=tenant_id)


class KPISnapshotRepository(BaseRepository[KPISnapshot]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, KPISnapshot, tenant_id=tenant_id)


class SavedReportRepository(BaseRepository[SavedReport]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, SavedReport, tenant_id=tenant_id)

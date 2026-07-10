"""
OpenS2P – Purchase Requisition repository
==========================================
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import (
    PRStatus,
    PurchaseRequisition,
    PurchaseRequisitionItem,
)
from app.repositories.base import BaseRepository


class PurchaseRequisitionRepository(BaseRepository[PurchaseRequisition]):
    """Tenant-scoped PR repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, PurchaseRequisition, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_by_number(self, pr_number: str) -> PurchaseRequisition | None:
        stmt = self._stmt().where(PurchaseRequisition.pr_number == pr_number)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_status(self, status: PRStatus) -> list[PurchaseRequisition]:
        stmt = self._stmt().where(PurchaseRequisition.status == status)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_requester(self, user_id: uuid.UUID) -> list[PurchaseRequisition]:
        stmt = self._stmt().where(PurchaseRequisition.requester_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_pending_approval(self) -> list[PurchaseRequisition]:
        """PRs submitted and awaiting approval."""
        return await self.list_by_status(PRStatus.SUBMITTED)

    async def get_with_items(
        self,
        pr_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> PurchaseRequisition | None:
        stmt = (
            self._stmt()
            .where(PurchaseRequisition.id == pr_id)
            .options(joinedload(PurchaseRequisition.items))
        )
        if not include_inactive:
            stmt = stmt.where(PurchaseRequisition.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()


class PurchaseRequisitionItemRepository(BaseRepository[PurchaseRequisitionItem]):
    """PR line-item repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, PurchaseRequisitionItem, tenant_id=tenant_id)

    async def list_by_requisition(
        self,
        requisition_id: uuid.UUID,
    ) -> list[PurchaseRequisitionItem]:
        stmt = self._stmt().where(
            PurchaseRequisitionItem.requisition_id == requisition_id,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

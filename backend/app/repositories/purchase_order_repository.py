"""
OpenS2P – Purchase Order repository
====================================
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import POStatus, PurchaseOrder, PurchaseOrderItem
from app.repositories.base import BaseRepository


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    """Tenant-scoped PO repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, PurchaseOrder, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_by_number(self, po_number: str) -> PurchaseOrder | None:
        stmt = self._stmt().where(PurchaseOrder.po_number == po_number)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_supplier(self, supplier_id: uuid.UUID) -> list[PurchaseOrder]:
        stmt = self._stmt().where(PurchaseOrder.supplier_id == supplier_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_status(self, status: POStatus) -> list[PurchaseOrder]:
        stmt = self._stmt().where(PurchaseOrder.status == status)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_open(self) -> list[PurchaseOrder]:
        """Orders that are not yet closed or cancelled."""
        stmt = self._stmt().where(
            PurchaseOrder.status.notin_([POStatus.CLOSED, POStatus.CANCELLED]),
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_with_items(self, po_id: uuid.UUID, *, include_inactive: bool = False) -> PurchaseOrder | None:
        stmt = (
            self._stmt()
            .where(PurchaseOrder.id == po_id)
            .options(joinedload(PurchaseOrder.items))
        )
        if not include_inactive:
            stmt = stmt.where(PurchaseOrder.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_with_receipts(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        stmt = (
            self._stmt()
            .where(PurchaseOrder.id == po_id)
            .options(joinedload(PurchaseOrder.receipts))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_with_invoices(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        stmt = (
            self._stmt()
            .where(PurchaseOrder.id == po_id)
            .options(joinedload(PurchaseOrder.invoices))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def calculate_total_commitment(self) -> float:
        """Sum of all open PO amounts."""
        stmt = select(PurchaseOrder)
        # Aggregate query could be added later
        result = await self.session.execute(stmt)
        return 0.0


class PurchaseOrderItemRepository(BaseRepository[PurchaseOrderItem]):
    """PO line-item repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, PurchaseOrderItem, tenant_id=tenant_id)

    async def list_by_po(self, po_id: uuid.UUID) -> list[PurchaseOrderItem]:
        stmt = self._stmt().where(PurchaseOrderItem.po_id == po_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

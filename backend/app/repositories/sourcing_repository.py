"""
OpenS2P – Sourcing repository
==============================
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import SourcingEvent, SupplierBid
from app.repositories.base import BaseRepository


class SourcingEventRepository(BaseRepository[SourcingEvent]):
    """Tenant-scoped sourcing event repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, SourcingEvent, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def list_by_type(self, event_type: str) -> list[SourcingEvent]:
        stmt = self._stmt().where(SourcingEvent.event_type == event_type)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_open(self) -> list[SourcingEvent]:
        """Events that are still accepting bids (close_date in the future)."""
        now = datetime.utcnow()
        stmt = self._stmt().where(
            SourcingEvent.close_date >= now,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_with_bids(self, event_id: uuid.UUID) -> SourcingEvent | None:
        stmt = (
            self._stmt()
            .where(SourcingEvent.id == event_id)
            .options(joinedload(SourcingEvent.bids))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()


class SupplierBidRepository(BaseRepository[SupplierBid]):
    """Tenant-scoped bid repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, SupplierBid, tenant_id=tenant_id)

    async def list_by_event(self, event_id: uuid.UUID) -> list[SupplierBid]:
        stmt = self._stmt().where(SupplierBid.event_id == event_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_supplier(self, supplier_id: uuid.UUID) -> list[SupplierBid]:
        stmt = self._stmt().where(SupplierBid.supplier_id == supplier_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_lowest_bid(self, event_id: uuid.UUID) -> SupplierBid | None:
        stmt = (
            self._stmt()
            .where(SupplierBid.event_id == event_id)
            .order_by(SupplierBid.bid_amount.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

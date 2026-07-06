"""
OpenS2P – Receiving repository
===============================
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Receipt
from app.repositories.base import BaseRepository


class ReceiptRepository(BaseRepository[Receipt]):
    """Tenant-scoped goods-receipt repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Receipt, tenant_id=tenant_id)

    async def list_by_po(self, po_id: uuid.UUID) -> list[Receipt]:
        stmt = self._stmt().where(Receipt.po_id == po_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_recent(self, days: int = 7) -> list[Receipt]:
        """Receipts recorded in the last N days."""
        since = date.today()
        stmt = self._stmt().where(Receipt.received_date >= since)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

"""
OpenS2P – Invoice repository
=============================
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invoice, MatchStatus
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    """Tenant-scoped invoice repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Invoice, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_by_number(self, invoice_number: str) -> Invoice | None:
        stmt = self._stmt().where(Invoice.invoice_number == invoice_number)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_po(self, po_id: uuid.UUID) -> list[Invoice]:
        stmt = self._stmt().where(Invoice.po_id == po_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_unpaid(self) -> list[Invoice]:
        """Invoices not yet fully paid."""
        stmt = self._stmt().where(
            Invoice.match_status.notin_([MatchStatus.MATCHED]),
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_exception_queue(self) -> list[Invoice]:
        """Invoices with matching exceptions that require human review."""
        stmt = self._stmt().where(Invoice.match_status == MatchStatus.EXCEPTION)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def find_duplicates(self, invoice: Invoice) -> list[Invoice]:
        """Potential duplicate invoices based on number and amount."""
        stmt = self._stmt().where(
            Invoice.invoice_number == invoice.invoice_number,
            Invoice.amount == invoice.amount,
            Invoice.id != invoice.id,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update_match_status(
        self,
        invoice_id: uuid.UUID,
        new_status: MatchStatus,
    ) -> Invoice | None:
        return await self.update(invoice_id, {"match_status": new_status})

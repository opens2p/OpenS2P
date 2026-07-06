"""
OpenS2P – Invoice Service
===========================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import Invoice, MatchStatus
from app.services.uow import UnitOfWork


class InvoiceService:
    """Invoice lifecycle and matching operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def submit_invoice(self, data: dict[str, Any]) -> Invoice:
        """Record a new invoice from a supplier."""
        invoice = await self.uow.invoices.create(data)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            event_type="INVOICE_SUBMITTED",
            new_values=data,
            created_by=self.actor_id,
        )
        return invoice

    async def perform_matching(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Execute 2-way and 3-way matching logic.

        2-way match:  invoice amount  vs  PO amount
        3-way match:  invoice amount  vs  PO amount AND receipt quantity
        """
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None

        # TODO: implement actual matching logic against PO and receipts
        # For now, auto-match as a placeholder
        updated = await self.uow.invoices.update_match_status(
            invoice_id, MatchStatus.MATCHED,
        )
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="invoice",
            entity_id=invoice_id,
            event_type="INVOICE_MATCHED",
            old_values={"match_status": invoice.match_status.value},
            new_values={"match_status": MatchStatus.MATCHED.value},
            created_by=self.actor_id,
        )
        return updated

    async def flag_exception(
        self,
        invoice_id: uuid.UUID,
        reason: str,
    ) -> Invoice | None:
        """Flag an invoice with a matching exception for review."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None
        old_status = invoice.match_status
        updated = await self.uow.invoices.update_match_status(
            invoice_id, MatchStatus.EXCEPTION,
        )
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="invoice",
            entity_id=invoice_id,
            event_type="INVOICE_EXCEPTION",
            old_values={"match_status": old_status.value},
            new_values={"match_status": MatchStatus.EXCEPTION.value, "reason": reason},
            created_by=self.actor_id,
        )
        return updated

    async def approve_payment(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Mark invoice as ready for payment."""
        return await self.uow.invoices.update(invoice_id, {
            "match_status": MatchStatus.MATCHED,
        })

    async def find_duplicates(self, invoice_id: uuid.UUID) -> list[Invoice]:
        """Detect potential duplicate invoices."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return []
        return await self.uow.invoices.find_duplicates(invoice)

    async def get_exception_queue(self) -> list[Invoice]:
        """Return all invoices requiring human review."""
        return await self.uow.invoices.list_exception_queue()

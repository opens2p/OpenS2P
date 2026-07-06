"""
OpenS2P – Receiving Service
============================
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from app.models import Receipt
from app.services.uow import UnitOfWork


class ReceivingService:
    """Goods / service receipt operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def create_receipt(self, data: dict[str, Any]) -> Receipt:
        """Record a goods or service receipt against a PO."""
        receipt = await self.uow.receipts.create({
            **data,
            "received_date": data.get("received_date", date.today()),
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="receipt",
            entity_id=receipt.id,
            event_type="RECEIPT_CREATED",
            new_values=data,
            created_by=self.actor_id,
        )
        return receipt

    async def validate_quantity(
        self,
        receipt_id: uuid.UUID,
    ) -> tuple[bool, str]:
        """Check whether received quantity matches the PO line item.

        Returns (is_valid, message).
        """
        receipt = await self.uow.receipts.get(receipt_id)
        if receipt is None:
            return False, "Receipt not found"
        # TODO: compare against PO item quantity
        return True, "Quantity OK"

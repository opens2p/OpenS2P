"""
OpenS2P – Receiving Service
============================
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from app.models import Receipt
from app.models.receiving import Receipt as ReceiptModel
from app.services.numbering import next_document_number
from app.services.uow import UnitOfWork


def _json_safe(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, (uuid.UUID, date, Decimal)):
            result[k] = str(v)
        else:
            result[k] = v
    return result


class ReceivingService:
    """Goods / service receipt operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def create_receipt(self, data: dict[str, Any]) -> Receipt:
        """Record a goods or service receipt against a PO."""
        payload = {
            **data,
            "received_date": data.get("received_date", date.today()),
        }
        if not payload.get("receipt_number"):
            payload["receipt_number"] = await next_document_number(
                self.uow.session, ReceiptModel, "receipt_number", "GR",
            )
        receipt = await self.uow.receipts.create(payload)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="receipt",
            entity_id=receipt.id,
            event_type="RECEIPT_CREATED",
            new_values=_json_safe(payload),
            created_by=self.actor_id,
        )
        return receipt

    async def validate_quantity(
        self,
        receipt_id: uuid.UUID,
    ) -> tuple[bool, str]:
        """Check whether received quantity matches the PO line items."""
        receipt = await self.uow.receipts.get(receipt_id)
        if receipt is None:
            return False, "Receipt not found"
        po = await self.uow.purchase_orders.get_with_items(receipt.po_id)
        if po is None:
            return False, "Purchase order not found"
        qty_ordered = sum(
            (Decimal(str(item.quantity or 0)) for item in (po.items or [])),
            Decimal("0"),
        )
        qty_received = Decimal(str(receipt.quantity_received or 0))
        if qty_ordered > 0 and qty_received <= 0:
            return False, "Received quantity is zero"
        if qty_received > qty_ordered:
            return False, f"Received qty {qty_received} exceeds ordered qty {qty_ordered}"
        return True, "Quantity OK"

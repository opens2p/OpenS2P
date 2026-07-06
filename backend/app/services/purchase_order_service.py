"""
OpenS2P – Purchase Order Service
==================================
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models import POStatus, PurchaseOrder
from app.services.uow import UnitOfWork


class PurchaseOrderService:
    """Purchase Order lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def create_po(self, data: dict[str, Any]) -> PurchaseOrder:
        """Create a PO from a purchase requisition or directly."""
        po = await self.uow.purchase_orders.create({
            **data,
            "status": POStatus.CREATED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po.id,
            event_type="PO_CREATED",
            new_values=data,
            created_by=self.actor_id,
        )
        return po

    async def send_to_supplier(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        """Mark PO as sent to the supplier."""
        po = await self.uow.purchase_orders.get(po_id)
        if po is None:
            return None
        old_status = po.status
        updated = await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.SENT,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po_id,
            event_type="PO_SENT",
            old_values={"status": old_status.value},
            new_values={"status": POStatus.SENT.value},
            created_by=self.actor_id,
        )
        return updated

    async def confirm_po(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        """Supplier has confirmed the PO."""
        return await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.CONFIRMED,
        })

    async def close_po(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        """Close a fully fulfilled PO."""
        po = await self.uow.purchase_orders.get(po_id)
        if po is None:
            return None
        old_status = po.status
        updated = await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.CLOSED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po_id,
            event_type="PO_CLOSED",
            old_values={"status": old_status.value},
            new_values={"status": POStatus.CLOSED.value},
            created_by=self.actor_id,
        )
        return updated

    async def cancel_po(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        """Cancel a PO."""
        return await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.CANCELLED,
        })

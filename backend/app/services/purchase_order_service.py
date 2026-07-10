"""
OpenS2P – Purchase Order Service
==================================
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models import POStatus, PurchaseOrder
from app.services.uow import UnitOfWork


def _status_value(status: POStatus | str | None) -> str | None:
    """Return enum value for PO status regardless of storage shape."""
    if status is None:
        return None
    if isinstance(status, POStatus):
        return status.value
    return str(status)


class PurchaseOrderService:
    """Purchase Order lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    @staticmethod
    def _serialize(value: Any) -> Any:
        """Convert non-JSON-serializable values to strings for audit logging."""
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    async def create_po(self, data: dict[str, Any]) -> PurchaseOrder:
        """Create a PO from a purchase requisition or directly."""
        # Remove items from data; they are created separately by the API layer
        data.pop("items", None)
        # Auto-generate PO number if not provided
        if not data.get("po_number"):
            from app.services.numbering import next_document_number
            from app.models.procurement import PurchaseOrder as POModel
            data["po_number"] = await next_document_number(
                self.uow.session, POModel, "po_number", "PO",
            )
        po = await self.uow.purchase_orders.create({
            **data,
            "status": POStatus.CREATED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po.id,
            event_type="PO_CREATED",
            new_values={k: self._serialize(v) for k, v in data.items()},
            created_by=self.actor_id,
        )
        return po

    async def delete_po(
        self,
        po_id: uuid.UUID,
        *,
        soft: bool = True,
    ) -> bool:
        """Soft-delete (or hard-delete) a purchase order."""
        po = await self.uow.purchase_orders.get(po_id)
        if po is None:
            return False
        deleted = await self.uow.purchase_orders.delete(po_id, soft=soft)
        if deleted:
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="purchase_order",
                entity_id=po_id,
                event_type="PO_DELETED",
                old_values={
                    "po_number": str(getattr(po, "po_number", "")),
                    "status": _status_value(getattr(po, "status", None)),
                },
                created_by=self.actor_id,
            )
        return deleted

    async def send_to_supplier(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        """Mark PO as sent to the supplier."""
        po = await self.uow.purchase_orders.get(po_id)
        if po is None:
            return None
        old_status = po.status
        await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.SENT,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po_id,
            event_type="PO_SENT",
            old_values={"status": _status_value(old_status)},
            new_values={"status": POStatus.SENT.value},
            created_by=self.actor_id,
        )
        return await self.uow.purchase_orders.get_with_items(po_id)

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
        await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.CLOSED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po_id,
            event_type="PO_CLOSED",
            old_values={"status": _status_value(old_status)},
            new_values={"status": POStatus.CLOSED.value},
            created_by=self.actor_id,
        )
        return await self.uow.purchase_orders.get_with_items(po_id)

    async def cancel_po(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        """Cancel a PO."""
        return await self.uow.purchase_orders.update(po_id, {
            "status": POStatus.CANCELLED,
        })

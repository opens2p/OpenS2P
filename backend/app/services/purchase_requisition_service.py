"""
OpenS2P – Purchase Requisition Service
========================================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import POStatus, PRStatus, PurchaseOrder, PurchaseRequisition
from app.services.uow import UnitOfWork


class PurchaseRequisitionError(Exception):
    """Business-rule violation in purchase requisition workflows."""


class SupplierRequiredError(PurchaseRequisitionError):
    """Raised when a supplier is required but missing."""


def _json_safe(data: dict) -> dict:
    """Convert non-JSON-serializable values (UUIDs, dates, etc.) to strings."""
    import uuid
    from datetime import datetime
    result = {}
    for k, v in data.items():
        if isinstance(v, (uuid.UUID, datetime)):
            result[k] = str(v)
        elif isinstance(v, dict):
            result[k] = _json_safe(v)
        elif isinstance(v, list):
            result[k] = [
                _json_safe(item) if isinstance(item, dict) else str(item)
                if isinstance(item, (uuid.UUID, datetime)) else item
                for item in v
            ]
        else:
            result[k] = v
    return result


def _status_value(status: PRStatus | str | None) -> str | None:
    """Return enum value for PR status regardless of storage shape."""
    if status is None:
        return None
    if isinstance(status, PRStatus):
        return status.value
    return str(status)


class PurchaseRequisitionService:
    """Purchase Requisition lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def submit_pr(self, data: dict[str, Any]) -> PurchaseRequisition:
        """Create and submit a PR for approval."""
        # Auto-generate PR number if not provided
        if not data.get("pr_number"):
            from app.services.numbering import next_document_number
            from app.models.procurement import PurchaseRequisition as PRModel
            data["pr_number"] = await next_document_number(
                self.uow.session, PRModel, "pr_number", "PR",
            )
        pr = await self.uow.purchase_requisitions.create({
            **data,
            "status": PRStatus.SUBMITTED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_requisition",
            entity_id=pr.id,
            event_type="PR_SUBMITTED",
            new_values=_json_safe(data),
            created_by=self.actor_id,
        )
        return pr

    async def _create_po_from_pr(self, pr: PurchaseRequisition) -> PurchaseOrder:
        """Create a PO from an approved PR and mark the PR as ORDERED."""
        if not pr.supplier_id:
            raise SupplierRequiredError(
                "A supplier must be assigned to the requisition before creating a purchase order",
            )
        if not pr.pr_number:
            raise PurchaseRequisitionError("Requisition is missing a PR number")

        from app.services.numbering import derive_po_number

        po_number = derive_po_number(pr.pr_number)
        existing = await self.uow.purchase_orders.get_by_number(po_number)
        if existing is not None:
            await self.uow.purchase_requisitions.update(pr.id, {
                "status": PRStatus.ORDERED,
            })
            return existing

        po = await self.uow.purchase_orders.create({
            "po_number": po_number,
            "supplier_id": pr.supplier_id,
            "status": POStatus.CREATED,
        })
        for item in pr.items or []:
            await self.uow.purchase_order_items.create({
                "po_id": po.id,
                "description": item.description,
                "quantity": item.quantity,
                "price": item.unit_price,
            })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_order",
            entity_id=po.id,
            event_type="PO_CREATED",
            new_values={
                "po_number": po_number,
                "supplier_id": str(pr.supplier_id),
                "requisition_id": str(pr.id),
            },
            created_by=self.actor_id,
        )
        await self.uow.purchase_requisitions.update(pr.id, {
            "status": PRStatus.ORDERED,
        })
        return po

    async def approve_pr(
        self,
        pr_id: uuid.UUID,
    ) -> PurchaseRequisition | None:
        """Approve a purchase requisition and auto-create a matching PO."""
        pr = await self.uow.purchase_requisitions.get_with_items(pr_id)
        if pr is None:
            return None
        if not pr.supplier_id:
            raise SupplierRequiredError(
                "A supplier must be assigned to the requisition before approval",
            )

        old_status = pr.status
        if pr.status != PRStatus.ORDERED:
            await self.uow.purchase_requisitions.update(pr_id, {
                "status": PRStatus.APPROVED,
            })
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="purchase_requisition",
                entity_id=pr_id,
                event_type="PR_APPROVED",
                old_values={"status": _status_value(old_status)},
                new_values={"status": PRStatus.APPROVED.value},
                created_by=self.actor_id,
            )

        await self._create_po_from_pr(pr)
        return await self.uow.purchase_requisitions.get_with_items(pr_id)

    async def create_po_from_pr(
        self,
        pr_id: uuid.UUID,
    ) -> PurchaseOrder | None:
        """Create a PO for an already-approved requisition."""
        pr = await self.uow.purchase_requisitions.get_with_items(pr_id)
        if pr is None:
            return None
        if pr.status not in {PRStatus.APPROVED, PRStatus.ORDERED}:
            raise PurchaseRequisitionError(
                "Purchase order can only be created from an approved requisition",
            )
        return await self._create_po_from_pr(pr)

    async def reject_pr(
        self,
        pr_id: uuid.UUID,
        reason: str | None = None,
    ) -> PurchaseRequisition | None:
        pr = await self.uow.purchase_requisitions.get(pr_id)
        if pr is None:
            return None
        old_status = pr.status
        await self.uow.purchase_requisitions.update(pr_id, {
            "status": PRStatus.REJECTED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_requisition",
            entity_id=pr_id,
            event_type="PR_REJECTED",
            old_values={"status": _status_value(old_status)},
            new_values={"status": PRStatus.REJECTED.value, "reason": reason},
            created_by=self.actor_id,
        )
        return await self.uow.purchase_requisitions.get_with_items(pr_id)

    async def delete_pr(
        self,
        pr_id: uuid.UUID,
        *,
        soft: bool = True,
    ) -> bool:
        pr = await self.uow.purchase_requisitions.get(pr_id)
        if pr is None:
            return False
        deleted = await self.uow.purchase_requisitions.delete(pr_id, soft=soft)
        if deleted:
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="purchase_requisition",
                entity_id=pr_id,
                event_type="PR_DELETED",
                old_values={
                    "pr_number": str(getattr(pr, "pr_number", "")),
                    "status": _status_value(getattr(pr, "status", None)),
                },
                created_by=self.actor_id,
            )
        return deleted

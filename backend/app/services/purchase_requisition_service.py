"""
OpenS2P – Purchase Requisition Service
========================================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import PRStatus, PurchaseRequisition
from app.services.uow import UnitOfWork


class PurchaseRequisitionService:
    """Purchase Requisition lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def submit_pr(self, data: dict[str, Any]) -> PurchaseRequisition:
        """Create and submit a PR for approval."""
        pr = await self.uow.purchase_requisitions.create({
            **data,
            "status": PRStatus.SUBMITTED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_requisition",
            entity_id=pr.id,
            event_type="PR_SUBMITTED",
            new_values=data,
            created_by=self.actor_id,
        )
        return pr

    async def approve_pr(
        self,
        pr_id: uuid.UUID,
    ) -> PurchaseRequisition | None:
        """Approve a purchase requisition."""
        pr = await self.uow.purchase_requisitions.get(pr_id)
        if pr is None:
            return None
        old_status = pr.status
        updated = await self.uow.purchase_requisitions.update(pr_id, {
            "status": PRStatus.APPROVED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_requisition",
            entity_id=pr_id,
            event_type="PR_APPROVED",
            old_values={"status": old_status.value},
            new_values={"status": PRStatus.APPROVED.value},
            created_by=self.actor_id,
        )
        return updated

    async def reject_pr(
        self,
        pr_id: uuid.UUID,
        reason: str | None = None,
    ) -> PurchaseRequisition | None:
        pr = await self.uow.purchase_requisitions.get(pr_id)
        if pr is None:
            return None
        old_status = pr.status
        updated = await self.uow.purchase_requisitions.update(pr_id, {
            "status": PRStatus.REJECTED,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="purchase_requisition",
            entity_id=pr_id,
            event_type="PR_REJECTED",
            old_values={"status": old_status.value},
            new_values={"status": PRStatus.REJECTED.value, "reason": reason},
            created_by=self.actor_id,
        )
        return updated

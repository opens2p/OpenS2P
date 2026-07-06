"""
OpenS2P – Supplier Service
===========================
Business rules for supplier onboarding, approval, risk scoring,
and lifecycle management.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import Supplier, SupplierStatus
from app.services.uow import UnitOfWork


class SupplierService:
    """Supplier lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id  # user performing the action

    # ── lifecycle ─────────────────────────────────────────────────────────

    async def onboard_supplier(self, data: dict[str, Any]) -> Supplier:
        """Register a new supplier in DRAFT status."""
        supplier = await self.uow.suppliers.create({
            **data,
            "status": SupplierStatus.DRAFT,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="supplier",
            entity_id=supplier.id,
            event_type="SUPPLIER_CREATED",
            new_values=data,
            created_by=self.actor_id,
        )
        return supplier

    async def approve_supplier(self, supplier_id: uuid.UUID) -> Supplier | None:
        """Approve a supplier after risk assessment."""
        supplier = await self.uow.suppliers.get(supplier_id)
        if supplier is None:
            return None

        old_status = supplier.status
        supplier = await self.uow.suppliers.update_status(
            supplier_id, SupplierStatus.APPROVED,
        )
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="supplier",
            entity_id=supplier_id,
            event_type="SUPPLIER_APPROVED",
            old_values={"status": old_status.value},
            new_values={"status": SupplierStatus.APPROVED.value},
            created_by=self.actor_id,
        )
        return supplier

    async def block_supplier(
        self,
        supplier_id: uuid.UUID,
        reason: str | None = None,
    ) -> Supplier | None:
        """Block a supplier (suspension)."""
        supplier = await self.uow.suppliers.get(supplier_id)
        if supplier is None:
            return None

        old_status = supplier.status
        supplier = await self.uow.suppliers.update_status(
            supplier_id, SupplierStatus.BLOCKED,
        )
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="supplier",
            entity_id=supplier_id,
            event_type="SUPPLIER_BLOCKED",
            old_values={"status": old_status.value},
            new_values={"status": SupplierStatus.BLOCKED.value, "reason": reason},
            created_by=self.actor_id,
        )
        return supplier

    # ── risk ──────────────────────────────────────────────────────────────

    async def calculate_risk_score(
        self,
        supplier_id: uuid.UUID,
    ) -> Decimal | None:
        """Placeholder for ML-based risk scoring.

        In production this would invoke a risk model that considers:
        * financial health scores
        * regulatory sanctions lists
        * past delivery performance
        * payment history
        """
        supplier = await self.uow.suppliers.get(supplier_id)
        if supplier is None:
            return None
        # TODO: integrate with AI risk model
        return supplier.risk_score

    # ── queries ───────────────────────────────────────────────────────────

    async def get_supplier_with_details(
        self,
        supplier_id: uuid.UUID,
    ) -> Supplier | None:
        """Fetch a supplier together with contacts and contracts."""
        return await self.uow.suppliers.get_with_contracts(supplier_id)

    async def search_suppliers(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Supplier]:
        return await self.uow.suppliers.search(query, skip=skip, limit=limit)

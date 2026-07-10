"""
Supplier scorecard analytics.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any
from app.services.uow import UnitOfWork


class SupplierScorecard:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def supplier_count(self) -> int:
        suppliers = await self.uow.suppliers.list(include_inactive=True)
        return len(suppliers)

    async def active_suppliers(self) -> int:
        from app.models import SupplierStatus
        suppliers = await self.uow.suppliers.list_by_status(SupplierStatus.APPROVED)
        return len(suppliers)

    async def risk_distribution(self) -> list[dict[str, Any]]:
        suppliers = await self.uow.suppliers.list(include_inactive=True)
        high = sum(1 for s in suppliers if s.risk_score and s.risk_score > 70)
        med = sum(1 for s in suppliers if s.risk_score and 30 < s.risk_score <= 70)
        low = sum(1 for s in suppliers if not s.risk_score or s.risk_score <= 30)
        return [{"level": "HIGH", "count": high}, {"level": "MEDIUM", "count": med}, {"level": "LOW", "count": low}]

    async def scorecard(self) -> dict[str, Any]:
        return {
            "total_suppliers": await self.supplier_count(),
            "active_suppliers": await self.active_suppliers(),
            "risk_distribution": await self.risk_distribution(),
        }

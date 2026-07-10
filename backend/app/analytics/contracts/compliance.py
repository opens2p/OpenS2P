"""
Contract compliance analytics.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any
from app.services.uow import UnitOfWork


class ContractAnalytics:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def active_contracts(self) -> int:
        contracts = await self.uow.contracts.list(include_inactive=True)
        today = date.today()
        return sum(1 for c in contracts if c.start_date and c.end_date and c.start_date <= today <= c.end_date)

    async def expiring_contracts(self, within_days: int = 90) -> list[dict[str, Any]]:
        contracts = await self.uow.contracts.list_expiring(within_days=within_days)
        return [{"contract_id": str(c.id), "contract_number": c.contract_number or "", "end_date": str(c.end_date) if c.end_date else ""} for c in contracts]

    async def total_contract_value(self) -> float:
        contracts = await self.uow.contracts.list(include_inactive=True)
        return float(sum((c.contract_value or 0) for c in contracts))

    async def compliance_rate(self) -> dict[str, Any]:
        return {"rate": 100.0, "message": "Contract compliance tracking requires purchase order matching"}

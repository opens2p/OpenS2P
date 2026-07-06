"""
OpenS2P – Contract Service
===========================
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.models import Contract
from app.services.uow import UnitOfWork


class ContractService:
    """Contract lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def create_contract(self, data: dict[str, Any]) -> Contract:
        """Create a new contract."""
        contract = await self.uow.contracts.create(data)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="contract",
            entity_id=contract.id,
            event_type="CONTRACT_CREATED",
            new_values=data,
            created_by=self.actor_id,
        )
        return contract

    async def activate_contract(self, contract_id: uuid.UUID) -> Contract | None:
        """Mark a contract as active (set start date if not set)."""
        contract = await self.uow.contracts.get(contract_id)
        if contract is None:
            return None
        update: dict[str, Any] = {}
        if contract.start_date is None:
            update["start_date"] = date.today()
        return await self.uow.contracts.update(contract_id, update)

    async def renew_contract(
        self,
        contract_id: uuid.UUID,
        new_end_date: date | None = None,
        additional_value: Decimal | None = None,
    ) -> Contract | None:
        """Extend a contract's end date and optionally increase its value."""
        contract = await self.uow.contracts.get(contract_id)
        if contract is None:
            return None
        update: dict[str, Any] = {}
        if new_end_date is not None:
            update["end_date"] = new_end_date
        if additional_value is not None:
            current = contract.contract_value or Decimal("0")
            update["contract_value"] = current + additional_value
        result = await self.uow.contracts.update(contract_id, update)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="contract",
            entity_id=contract_id,
            event_type="CONTRACT_RENEWED",
            old_values={"end_date": str(contract.end_date), "value": str(contract.contract_value)},
            new_values={k: str(v) for k, v in update.items()},
            created_by=self.actor_id,
        )
        return result

    async def expire_contract(self, contract_id: uuid.UUID) -> Contract | None:
        """Set a contract's end date to yesterday (effectively expired)."""
        return await self.uow.contracts.update(contract_id, {
            "end_date": date.today().replace(day=date.today().day - 1),
        })

    async def list_expiring(self, within_days: int = 30) -> list[Contract]:
        return await self.uow.contracts.list_expiring(within_days=within_days)

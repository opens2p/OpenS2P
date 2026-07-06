"""
OpenS2P – Contract repository
==============================
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract
from app.repositories.base import BaseRepository


class ContractRepository(BaseRepository[Contract]):
    """Tenant-scoped contract repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Contract, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_by_number(self, contract_number: str) -> Contract | None:
        stmt = self._stmt().where(Contract.contract_number == contract_number)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_supplier(self, supplier_id: uuid.UUID) -> list[Contract]:
        stmt = self._stmt().where(Contract.supplier_id == supplier_id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_active(self) -> list[Contract]:
        """Contracts that are currently in effect."""
        today = date.today()
        stmt = self._stmt().where(
            Contract.start_date <= today,
            Contract.end_date >= today,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_expiring(
        self,
        within_days: int = 30,
    ) -> list[Contract]:
        """Contracts expiring within the given number of days."""
        today = date.today()
        stmt = self._stmt().where(
            Contract.end_date.between(today, today.replace(day=today.day + within_days)),
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_value_range(
        self,
        min_value: float,
        max_value: float,
    ) -> list[Contract]:
        stmt = self._stmt().where(
            Contract.contract_value >= min_value,
            Contract.contract_value <= max_value,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

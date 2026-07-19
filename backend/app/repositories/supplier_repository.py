"""
OpenS2P – Supplier repository
===============================
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Supplier, SupplierStatus
from app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    """Tenant-scoped supplier repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Supplier, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_by_number(self, supplier_number: str) -> Supplier | None:
        stmt = self._stmt().where(Supplier.supplier_number == supplier_number)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Supplier]:
        stmt = self._stmt().where(
            or_(
                Supplier.supplier_name.ilike(f"%{query}%"),
                Supplier.supplier_number.ilike(f"%{query}%"),
            ),
        )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_status(
        self,
        status: SupplierStatus,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Supplier]:
        stmt = (
            self._stmt()
            .where(Supplier.status == status)
            .where(Supplier.is_active.is_(True))
            .order_by(Supplier.supplier_name.asc())
        )
        stmt = stmt.offset(skip).limit(min(limit, 200))
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_high_risk(self, threshold: float = 70.0) -> list[Supplier]:
        """Suppliers whose risk score exceeds the threshold."""
        stmt = self._stmt().where(Supplier.risk_score >= threshold)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update_status(
        self,
        supplier_id: uuid.UUID,
        new_status: SupplierStatus,
    ) -> Supplier | None:
        return await self.update(supplier_id, {"status": new_status})

    # ── eager-loading variants ────────────────────────────────────────────

    async def get_with_contacts(self, supplier_id: uuid.UUID) -> Supplier | None:
        stmt = (
            self._stmt()
            .where(Supplier.id == supplier_id)
            .options(joinedload(Supplier.contacts))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_with_documents(self, supplier_id: uuid.UUID) -> Supplier | None:
        stmt = (
            self._stmt()
            .where(Supplier.id == supplier_id)
            .options(joinedload(Supplier.documents))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_with_contracts(self, supplier_id: uuid.UUID) -> Supplier | None:
        stmt = (
            self._stmt()
            .where(Supplier.id == supplier_id)
            .options(joinedload(Supplier.contracts))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

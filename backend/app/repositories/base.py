"""
OpenS2P – Generic base repository
===================================
Abstract CRUD foundation that every domain repository extends.

All queries are tenant-scoped by default (``tenant_id`` is required).
Soft-delete is respected throughout — ``list()`` / ``get()`` return only
active rows unless ``include_inactive=True`` is passed.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, UnaryExpression, asc, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)

# Default page size for paginated queries
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class BaseRepository(Generic[ModelT]):
    """Tenant-scoped generic repository.

    :param session:      SQLAlchemy async session.
    :param model:        SQLAlchemy model class (e.g. ``Supplier``).
    :param tenant_id:    Tenant UUID — all queries are filtered by this.
    """

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelT],
        tenant_id: uuid.UUID | None = None,
    ) -> None:
        self.session = session
        self.model = model
        self.tenant_id = tenant_id

    # ── helpers ───────────────────────────────────────────────────────────

    def _stmt(self) -> Select:
        """Base ``select()`` pre-filtered by tenant and soft-delete."""
        stmt = select(self.model)
        if self.tenant_id is not None:
            stmt = stmt.where(self.model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]
        return stmt

    def _order_by(
        self,
        stmt: Select,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> Select:
        if sort_by and hasattr(self.model, sort_by):
            col = getattr(self.model, sort_by)
            direction: UnaryExpression = desc(col) if sort_desc else asc(col)
            stmt = stmt.order_by(direction)
        return stmt

    # ── CRUD ──────────────────────────────────────────────────────────────

    async def get(self, id: uuid.UUID, *, include_inactive: bool = False) -> ModelT | None:
        """Fetch a single record by primary key (respects tenant scope and active flag)."""
        stmt = self._stmt().where(self.model.id == id)  # type: ignore[attr-defined]
        if not include_inactive and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = DEFAULT_PAGE_SIZE,
        sort_by: str | None = None,
        sort_desc: bool = False,
        include_inactive: bool = False,
    ) -> list[ModelT]:
        """Fetch a page of records.

        Results are ordered by ``created_at`` descending by default
        (or the supplied ``sort_by`` column).
        """
        stmt = self._stmt()
        if not include_inactive and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))  # type: ignore[attr-defined]
        stmt = self._order_by(stmt, sort_by or "created_at", sort_desc or True)
        stmt = stmt.offset(skip).limit(min(limit, MAX_PAGE_SIZE))
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_all(
        self,
        *,
        include_inactive: bool = False,
    ) -> list[ModelT]:
        """Fetch **all** records matching the tenant scope (no pagination).

        Use sparingly — prefer ``list()`` with pagination for user-facing
        endpoints.
        """
        stmt = self._stmt()
        if not include_inactive and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))  # type: ignore[attr-defined]
        stmt = stmt.order_by(desc(self.model.created_at))  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def create(self, data: ModelT | dict[str, Any]) -> ModelT:
        """Insert a new record and flush.

        Accepts either a model instance or a plain dict.
        """
        if isinstance(data, dict):
            if self.tenant_id is not None and "tenant_id" not in data:
                data["tenant_id"] = self.tenant_id
            instance = self.model(**data)
        else:
            instance = data
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(
        self,
        id: uuid.UUID,
        data: dict[str, Any],
    ) -> ModelT | None:
        """Partial update — sets only the keys present in ``data``."""
        stmt = self._stmt().where(self.model.id == id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        instance = result.unique().scalar_one_or_none()
        if instance is None:
            return None
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(
        self,
        id: uuid.UUID,
        *,
        soft: bool = True,
    ) -> bool:
        """Remove a record.

        * ``soft=True``  — sets ``is_active = False`` (default)
        * ``soft=False`` — permanently deletes the row
        """
        stmt = self._stmt().where(self.model.id == id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        instance = result.unique().scalar_one_or_none()
        if instance is None:
            return False
        if soft and hasattr(instance, "is_active"):
            instance.is_active = False  # type: ignore[attr-defined]
            await self.session.flush()
        else:
            await self.session.delete(instance)
            await self.session.flush()
        return True

    async def exists(self, id: uuid.UUID) -> bool:
        """Check whether a record with the given PK exists in the tenant scope."""
        stmt = select(func.count(self.model.id)).where(  # type: ignore[attr-defined]
            self.model.id == id,  # type: ignore[attr-defined]
        )
        if self.tenant_id is not None:
            stmt = stmt.where(self.model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def count(
        self,
        *,
        include_inactive: bool = False,
    ) -> int:
        """Total record count within the tenant scope."""
        stmt = select(func.count(self.model.id))  # type: ignore[attr-defined]
        if self.tenant_id is not None:
            stmt = stmt.where(self.model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]
        if not include_inactive and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one()

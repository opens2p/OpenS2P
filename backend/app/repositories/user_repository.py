"""
OpenS2P – User repository
==========================
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Role, User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Tenant-scoped user repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, User, tenant_id=tenant_id)

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> User | None:
        stmt = self._stmt().where(User.email == email)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = self._stmt().where(User.username == username)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def search(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[User]:
        """Full-text-ish search across name and email fields."""
        stmt = self._stmt().where(
            or_(
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%"),
            ),
        )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    # ── role management ───────────────────────────────────────────────────

    async def get_with_roles(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user eagerly loaded with their role assignments."""
        stmt = (
            self._stmt()
            .where(User.id == user_id)
            .options(joinedload(User.roles).joinedload(UserRole.role))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> UserRole:
        """Assign a role to a user."""
        ur = UserRole(
            user_id=user_id,
            role_id=role_id,
            tenant_id=self.tenant_id,
        )
        self.session.add(ur)
        await self.session.flush()
        return ur

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        result = await self.session.execute(stmt)
        ur = result.unique().scalar_one_or_none()
        if ur is None:
            return False
        await self.session.delete(ur)
        await self.session.flush()
        return True

    async def list_by_role(self, role_name: str) -> list[User]:
        """Return all users who have the specified role."""
        stmt = (
            self._stmt()
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.role_name == role_name)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

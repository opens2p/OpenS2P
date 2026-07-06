from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base


class Role(Base, AuditMixin):
    """Named role for RBAC within a tenant."""

    __tablename__ = "roles"

    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # -- relationships -------------------------------------------------------
    user_assignments: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan",
    )


class UserRole(Base, AuditMixin):
    """Many-to-many association between users and roles."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True,
    )

    # -- relationships -------------------------------------------------------
    user: Mapped["User"] = relationship(
        "User", back_populates="roles", foreign_keys="UserRole.user_id",
    )
    role: Mapped["Role"] = relationship(
        "Role", back_populates="user_assignments",
    )

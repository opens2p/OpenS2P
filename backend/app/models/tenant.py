from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantStatus


class Tenant(Base):
    """Top-level multi-tenant organisation."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    tenant_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus), nullable=False, server_default=TenantStatus.ACTIVE.value,
    )

    # -- audit fields (Tenant doesn't inherit AuditMixin because it IS the root)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")

    # -- relationships -------------------------------------------------------
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan",
    )
    suppliers: Mapped[List["Supplier"]] = relationship(
        "Supplier", back_populates="tenant", cascade="all, delete-orphan",
    )
    sourcing_events: Mapped[List["SourcingEvent"]] = relationship(
        "SourcingEvent", back_populates="tenant", cascade="all, delete-orphan",
    )
    contracts: Mapped[List["Contract"]] = relationship(
        "Contract", back_populates="tenant", cascade="all, delete-orphan",
    )
    purchase_requisitions: Mapped[List["PurchaseRequisition"]] = relationship(
        "PurchaseRequisition", back_populates="tenant", cascade="all, delete-orphan",
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="tenant", cascade="all, delete-orphan",
    )

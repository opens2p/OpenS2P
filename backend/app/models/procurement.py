from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Enum, Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base, PRStatus, POStatus


# =========================================================================
# PURCHASE REQUISITION
# =========================================================================


class PurchaseRequisition(Base, AuditMixin):
    """Internal request to procure goods / services."""

    __tablename__ = "purchase_requisitions"

    pr_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    status: Mapped[PRStatus] = mapped_column(
        Enum(PRStatus), nullable=False, server_default=PRStatus.DRAFT.value,
    )
    requester_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True, index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)

    # -- relationships -------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="purchase_requisitions")

    items: Mapped[List["PurchaseRequisitionItem"]] = relationship(
        "PurchaseRequisitionItem", back_populates="requisition", cascade="all, delete-orphan",
    )


class PurchaseRequisitionItem(Base, AuditMixin):
    """Line item on a purchase requisition."""

    __tablename__ = "purchase_requisition_items"

    requisition_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=False, index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # -- relationships -------------------------------------------------------
    requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition", back_populates="items",
    )


# =========================================================================
# PURCHASE ORDER
# =========================================================================


class PurchaseOrder(Base, AuditMixin):
    """Order sent to a supplier."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True,
    )
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus), nullable=False, server_default=POStatus.CREATED.value,
    )

    # -- relationships -------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="purchase_orders")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")

    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan",
    )
    receipts: Mapped[List["Receipt"]] = relationship(
        "Receipt", back_populates="purchase_order",
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="purchase_order",
    )


class PurchaseOrderItem(Base, AuditMixin):
    """Line item on a purchase order."""

    __tablename__ = "purchase_order_items"

    po_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # -- relationships -------------------------------------------------------
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="items",
    )

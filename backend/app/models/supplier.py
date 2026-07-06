from __future__ import annotations

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Enum, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base, SupplierStatus


class Supplier(Base, AuditMixin):
    """Vendor / supplier master record."""

    __tablename__ = "suppliers"

    supplier_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SupplierStatus] = mapped_column(
        Enum(SupplierStatus), nullable=False, server_default=SupplierStatus.DRAFT.value,
    )
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    extras: Mapped[dict | None] = mapped_column(JSONB)

    # -- relationships -------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="suppliers")

    contacts: Mapped[List["SupplierContact"]] = relationship(
        "SupplierContact", back_populates="supplier", cascade="all, delete-orphan",
    )
    documents: Mapped[List["SupplierDocument"]] = relationship(
        "SupplierDocument", back_populates="supplier", cascade="all, delete-orphan",
    )
    contracts: Mapped[List["Contract"]] = relationship(
        "Contract", back_populates="supplier",
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="supplier",
    )
    bids: Mapped[List["SupplierBid"]] = relationship(
        "SupplierBid", back_populates="supplier",
    )


class SupplierContact(Base, AuditMixin):
    """Contact person for a supplier."""

    __tablename__ = "supplier_contacts"

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True,
    )
    contact_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(255))

    # -- relationships -------------------------------------------------------
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="contacts")


class SupplierDocument(Base, AuditMixin):
    """Attachment / document linked to a supplier."""

    __tablename__ = "supplier_documents"

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True,
    )
    document_name: Mapped[str | None] = mapped_column(String(255))
    document_url: Mapped[str | None] = mapped_column(String(2000))
    extras: Mapped[dict | None] = mapped_column(JSONB)

    # -- relationships -------------------------------------------------------
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="documents")

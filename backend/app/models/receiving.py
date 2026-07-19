from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base


class Receipt(Base, AuditMixin):
    """Goods / service receipt against a purchase order."""

    __tablename__ = "receipts"

    receipt_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    po_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, index=True,
    )
    received_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(50))
    quantity_received: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    amount_received: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # -- relationships -------------------------------------------------------
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="receipts",
    )

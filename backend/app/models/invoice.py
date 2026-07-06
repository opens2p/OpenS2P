from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base, MatchStatus


class Invoice(Base, AuditMixin):
    """Supplier invoice referencing a purchase order."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str | None] = mapped_column(String(100))
    po_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), nullable=False, server_default=MatchStatus.PENDING.value,
    )
    invoice_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    extras: Mapped[dict | None] = mapped_column(JSONB)

    # -- relationships -------------------------------------------------------
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="invoices",
    )

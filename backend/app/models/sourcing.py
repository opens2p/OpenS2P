from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base


class SourcingEvent(Base, AuditMixin):
    """RFQ / RFP / Auction event."""

    __tablename__ = "sourcing_events"

    event_name: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(50))  # RFQ / RFP / AUCTION
    status: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    open_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # -- relationships -------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="sourcing_events")

    bids: Mapped[List["SupplierBid"]] = relationship(
        "SupplierBid", back_populates="sourcing_event", cascade="all, delete-orphan",
    )


class SupplierBid(Base, AuditMixin):
    """Bid submitted by a supplier for a sourcing event."""

    __tablename__ = "supplier_bids"

    event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sourcing_events.id"), nullable=False, index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True,
    )
    bid_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extras: Mapped[dict | None] = mapped_column(JSONB)

    # -- relationships -------------------------------------------------------
    sourcing_event: Mapped["SourcingEvent"] = relationship(
        "SourcingEvent", back_populates="bids",
    )
    supplier: Mapped["Supplier"] = relationship(
        "Supplier", back_populates="bids",
    )

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date
from typing import Optional

from sqlalchemy import Date, DateTime, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base


class Contract(Base, AuditMixin):
    """Procurement contract with a supplier."""

    __tablename__ = "contracts"

    contract_number: Mapped[str | None] = mapped_column(String(100))
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True,
    )
    contract_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)

    # -- relationships -------------------------------------------------------
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="contracts")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="contracts")

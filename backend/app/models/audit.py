from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AuditEvent(Base):
    """Immutable audit trail for every meaningful state change.

    Enterprise procurement systems require point-in-time answers to:
    * "Who changed the supplier bank account?"
    * "What was the PO amount before it was modified?"
    * "When was the contract approved and by whom?"

    This table stores a permanent record of every action so those
    questions can be answered without relying on application logs.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # -- indexes for common query patterns --------------------------------
    __table_args__ = (
        Index("ix_audit_events_lookup", "entity_type", "entity_id"),
        Index("ix_audit_events_timeline", "tenant_id", "created_at"),
    )

    # -- relationships (read-only, no back-populates needed) ---------------
    tenant: Mapped["Tenant"] = relationship("Tenant")

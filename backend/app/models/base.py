from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums aligned with docs/03_engineering/database/schema/constraints.sql
# ---------------------------------------------------------------------------


class SupplierStatus(PyEnum):
    """CHECK constraint: status IN ('DRAFT','INVITED','REGISTERED','APPROVED','BLOCKED')"""

    DRAFT = "DRAFT"
    INVITED = "INVITED"
    REGISTERED = "REGISTERED"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"


class PRStatus(PyEnum):
    """CHECK constraint: status IN ('DRAFT','SUBMITTED','APPROVED','REJECTED','ORDERED')"""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ORDERED = "ORDERED"


class POStatus(PyEnum):
    """Purchase order lifecycle statuses."""

    CREATED = "CREATED"
    APPROVED = "APPROVED"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class MatchStatus(PyEnum):
    """CHECK constraint: match_status IN ('PENDING','MATCHED','EXCEPTION')"""

    PENDING = "PENDING"
    MATCHED = "MATCHED"
    EXCEPTION = "EXCEPTION"


class InvoiceStatus(PyEnum):
    """Application-level invoice lifecycle."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class WorkflowStatus(PyEnum):
    """CHECK constraint: n/a (app-level), aligned with workflow engine."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TenantStatus(PyEnum):
    """CHECK constraint: status IN ('ACTIVE','INACTIVE','SUSPENDED')"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# ---------------------------------------------------------------------------
# Audit Mixin  (allows tenant isolation on every business table)
# ---------------------------------------------------------------------------


class AuditMixin:
    """Mixin providing UUID PK, tenant FK, audit timestamps, and soft-delete flag.

    Every business table that inherits this mixin automatically gains:
    * ``id``             – UUID primary key
    * ``tenant_id``      – foreign key to ``tenants.id`` (required)
    * ``created_at``     – server-side UTC timestamp
    * ``created_by``     – FK to ``users.id`` (optional)
    * ``updated_at``     – server-side UTC timestamp, refreshed on update
    * ``updated_by``     – FK to ``users.id`` (optional)
    * ``is_active``      – soft-delete / deactivation flag
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true",
    )

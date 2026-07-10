from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import AuditMixin, Base


class IntegrationConnection(Base, AuditMixin):
    """Stored connection details for an external system."""
    __tablename__ = "integration_connections"

    connection_name: Mapped[str] = mapped_column(String(200), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)  # sap, coupa, oracle, netsuite, generic_rest
    endpoint_url: Mapped[str | None] = mapped_column(String(2000))
    auth_type: Mapped[str | None] = mapped_column(String(50))  # basic, oauth2, api_key, certificate
    credentials: Mapped[dict | None] = mapped_column(JSONB)  # encrypted in production
    config: Mapped[dict | None] = mapped_column(JSONB)  # connector-specific settings
    is_connected: Mapped[bool] = mapped_column(Boolean, server_default="false")
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IntegrationRun(Base, AuditMixin):
    """Record of a sync execution."""
    __tablename__ = "integration_runs"

    connection_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("integration_connections.id"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # extract, load
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # running, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int | None] = mapped_column(Integer)
    errors: Mapped[dict | None] = mapped_column(JSONB)

    connection: Mapped["IntegrationConnection"] = relationship("IntegrationConnection")


class IntegrationLog(Base):
    """Detailed log entry for an integration run."""
    __tablename__ = "integration_logs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("integration_runs.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO, WARN, ERROR
    message: Mapped[str] = mapped_column(Text, nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(100))
    object_id: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FieldMapping(Base, AuditMixin):
    """Field-level mapping between external system and OpenS2P."""
    __tablename__ = "field_mappings"

    connection_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("integration_connections.id"), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)  # supplier, purchase_order, invoice
    external_field: Mapped[str] = mapped_column(String(200), nullable=False)
    internal_field: Mapped[str] = mapped_column(String(200), nullable=False)
    transform_expression: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    connection: Mapped["IntegrationConnection"] = relationship("IntegrationConnection")


class ExternalReference(Base):
    """Maps OpenS2P UUIDs to external system IDs."""
    __tablename__ = "external_references"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    connection_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("integration_connections.id"), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    internal_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_system: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

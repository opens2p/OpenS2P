from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import AuditMixin, Base


class Document(Base, AuditMixin):
    """File/document attached to a business object."""
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(2000), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(50), server_default="local")
    object_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # supplier, contract, invoice, sourcing_event
    object_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100))  # contract_pdf, invoice_pdf, specification, etc.
    description: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(String(64))
    is_latest: Mapped[bool] = mapped_column(Boolean, server_default="true")
    doc_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentVersion(Base):
    """Version tracking for documents."""
    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(2000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(64))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

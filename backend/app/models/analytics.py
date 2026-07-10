from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import AuditMixin, Base


class KPIDefinition(Base):
    """Defines a key performance indicator that can be calculated."""
    __tablename__ = "kpi_definitions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    kpi_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # spend, supplier, contract, process
    unit: Mapped[str | None] = mapped_column(String(50))  # USD, count, days, percentage
    higher_is_better: Mapped[bool] = mapped_column(Boolean, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KPISnapshot(Base):
    """Point-in-time KPI value with trend data."""
    __tablename__ = "kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    kpi_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    previous_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dimension: Mapped[str | None] = mapped_column(String(100))  # e.g. supplier_id, category, department
    dimension_value: Mapped[str | None] = mapped_column(String(255))
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DashboardConfig(Base, AuditMixin):
    """Saved dashboard layout configuration."""
    __tablename__ = "dashboard_configs"

    dashboard_name: Mapped[str] = mapped_column(String(200), nullable=False)
    layout: Mapped[dict] = mapped_column(JSONB, nullable=False)  # widget positions, sizes
    is_default: Mapped[bool] = mapped_column(Boolean, server_default="false")


class SavedReport(Base, AuditMixin):
    """User-saved report configuration."""
    __tablename__ = "saved_reports"

    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # spend, supplier, contract, custom
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)  # filters, groupings, metrics
    schedule_cron: Mapped[str | None] = mapped_column(String(100))  # optional cron for auto-generation
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReportExecution(Base, AuditMixin):
    """Record of a report generation run."""
    __tablename__ = "report_executions"

    report_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("saved_reports.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # running, completed, failed
    output_format: Mapped[str | None] = mapped_column(String(20))  # csv, excel, pdf
    output_path: Mapped[str | None] = mapped_column(String(2000))
    record_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

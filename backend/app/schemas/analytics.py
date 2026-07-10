"""
Analytics Pydantic schemas.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class KPIDefinitionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    kpi_name: str
    display_name: str
    description: str | None = None
    category: str
    unit: str | None = None
    higher_is_better: bool = True


class KPISnapshotResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    kpi_name: str
    value: float
    previous_value: float | None = None
    period: str
    dimension: str | None = None
    dimension_value: str | None = None


class DashboardResponse(BaseModel):
    kpi_summary: dict[str, Any]
    spend: dict[str, Any]
    suppliers: dict[str, Any]
    cycle_times: dict[str, Any]
    contracts: dict[str, Any]


class SavedReportCreate(BaseModel):
    report_name: str
    report_type: str
    config: dict[str, Any]


class SavedReportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    report_name: str
    report_type: str
    config: dict[str, Any]
    last_run_at: datetime | None = None
    created_at: datetime | None = None
    tenant_id: uuid.UUID

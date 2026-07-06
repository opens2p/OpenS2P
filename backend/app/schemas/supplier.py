"""
OpenS2P – Supplier schemas
===========================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import SupplierStatus
from app.schemas.common import AuditFields


# ── requests ──────────────────────────────────────────────────────────────


class SupplierCreate(BaseModel):
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_number: str | None = None
    description: str | None = None
    address: str | None = None
    risk_score: Decimal | None = None
    extras: dict[str, Any] | None = None


class SupplierUpdate(BaseModel):
    supplier_name: str | None = None
    description: str | None = None
    address: str | None = None
    extras: dict[str, Any] | None = None


# ── responses ─────────────────────────────────────────────────────────────


class SupplierResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    supplier_name: str
    supplier_number: str | None = None
    status: SupplierStatus
    risk_score: Decimal | None = None
    description: str | None = None
    address: str | None = None
    extras: dict[str, Any] | None = None
    tenant_id: uuid.UUID


class SupplierSummary(BaseModel):
    """Lightweight supplier representation for list endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    supplier_name: str
    supplier_number: str | None = None
    status: SupplierStatus
    risk_score: Decimal | None = None

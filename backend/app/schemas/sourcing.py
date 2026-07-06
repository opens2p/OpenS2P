"""
OpenS2P – Sourcing schemas
===========================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuditFields


class SourcingEventCreate(BaseModel):
    event_name: str | None = None
    event_type: str | None = None
    description: str | None = None
    open_date: datetime | None = None
    close_date: datetime | None = None


class SourcingEventResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_name: str | None = None
    event_type: str | None = None
    status: str | None = None
    description: str | None = None
    open_date: datetime | None = None
    close_date: datetime | None = None
    tenant_id: uuid.UUID


class BidCreate(BaseModel):
    supplier_id: uuid.UUID
    bid_amount: Decimal = Field(..., ge=0)
    extras: dict[str, Any] | None = None


class BidResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    supplier_id: uuid.UUID
    bid_amount: Decimal | None = None
    submitted_at: datetime | None = None
    extras: dict[str, Any] | None = None
    tenant_id: uuid.UUID


class AwardRequest(BaseModel):
    supplier_id: uuid.UUID

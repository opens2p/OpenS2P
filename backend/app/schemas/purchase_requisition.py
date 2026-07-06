"""
OpenS2P – Purchase Requisition schemas
========================================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import PRStatus
from app.schemas.common import AuditFields


class PurchaseRequisitionItemCreate(BaseModel):
    description: str | None = None
    quantity: Decimal | None = Field(None, ge=0)
    unit_price: Decimal | None = Field(None, ge=0)


class PurchaseRequisitionItemResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requisition_id: uuid.UUID
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None


class PurchaseRequisitionCreate(BaseModel):
    description: str | None = None
    items: list[PurchaseRequisitionItemCreate] = []


class PurchaseRequisitionResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pr_number: str | None = None
    status: PRStatus
    requester_id: uuid.UUID | None = None
    description: str | None = None
    tenant_id: uuid.UUID
    items: list[PurchaseRequisitionItemResponse] | None = None

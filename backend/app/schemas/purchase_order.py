"""
OpenS2P – Purchase Order schemas
==================================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import POStatus
from app.schemas.common import AuditFields


class PurchaseOrderItemCreate(BaseModel):
    description: str | None = None
    quantity: Decimal | None = Field(None, ge=0)
    price: Decimal | None = Field(None, ge=0)


class PurchaseOrderItemResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_id: uuid.UUID
    description: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: uuid.UUID
    items: list[PurchaseOrderItemCreate] = []


class PurchaseOrderResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_number: str | None = None
    supplier_id: uuid.UUID
    status: POStatus
    tenant_id: uuid.UUID
    items: list[PurchaseOrderItemResponse] | None = None

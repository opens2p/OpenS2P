"""
OpenS2P – Contract schemas
===========================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuditFields


class ContractCreate(BaseModel):
    contract_number: str | None = None
    supplier_id: uuid.UUID
    contract_value: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class ContractUpdate(BaseModel):
    contract_value: Decimal | None = None
    end_date: date | None = None
    description: str | None = None


class ContractRenew(BaseModel):
    new_end_date: date | None = None
    additional_value: Decimal | None = None


class ContractResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_number: str | None = None
    supplier_id: uuid.UUID
    contract_value: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    tenant_id: uuid.UUID

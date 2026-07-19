"""
OpenS2P – Invoice schemas
==========================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import MatchStatus
from app.schemas.common import AuditFields


class InvoiceCreate(BaseModel):
    invoice_number: str | None = None
    po_id: uuid.UUID
    amount: Decimal = Field(..., ge=0)
    invoice_date: date | None = None
    due_date: date | None = None
    extras: dict[str, Any] | None = None


class InvoiceResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str | None = None
    po_id: uuid.UUID
    amount: Decimal
    match_status: MatchStatus
    invoice_date: date | None = None
    due_date: date | None = None
    extras: dict[str, Any] | None = None
    tenant_id: uuid.UUID


class InvoiceUpdate(BaseModel):
    invoice_number: str | None = None
    amount: Decimal | None = Field(None, ge=0)
    invoice_date: date | None = None
    due_date: date | None = None
    extras: dict[str, Any] | None = None


class MatchAction(BaseModel):
    """Trigger 2-way / 3-way matching."""
    action: str = "match"  # match | flag_exception


class ResolveExceptionRequest(BaseModel):
    """Clear an invoice matching exception."""
    mode: str = Field("auto", pattern="^(auto|manual)$")
    note: str | None = None


class PaymentApproval(BaseModel):
    approved: bool = True
    notes: str | None = None

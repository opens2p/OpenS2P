"""
OpenS2P – Receiving API endpoints
===================================
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.schemas.serialization import safe_validate
from app.services.receiving_service import ReceivingService

router = APIRouter(prefix="/receiving", tags=["Receiving"])


class ReceiptResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    receipt_number: str | None = None
    po_id: uuid.UUID
    status: str | None = None
    received_date: date | None = None
    quantity_received: Decimal | None = None
    amount_received: Decimal | None = None
    tenant_id: uuid.UUID
    created_at: datetime | None = None


class ReceiptCreate(BaseModel):
    po_id: uuid.UUID
    status: str = "completed"
    quantity_received: Decimal | None = Field(None, ge=0)
    amount_received: Decimal | None = Field(None, ge=0)
    received_date: date | None = None


@router.get("/receipts", response_model=ApiResponse[list[ReceiptResponse]])
async def list_receipts(
    _: AuthContext = Depends(require_permission(perm.PO_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        receipts = await uow.receipts.list()
        return ApiResponse(data=[await safe_validate(ReceiptResponse, r) for r in receipts])


@router.post("/receipts", response_model=ApiResponse[ReceiptResponse], status_code=201)
async def create_receipt(
    body: ReceiptCreate,
    _: None = Depends(require_permission(perm.PO_UPDATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        po = await uow.purchase_orders.get_with_items(body.po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        payload = body.model_dump(exclude_none=True)
        # Default qty to full PO ordered qty when status is completed and qty omitted
        if payload.get("quantity_received") is None and po.items:
            ordered = sum((item.quantity or 0) for item in po.items)
            if body.status == "completed":
                payload["quantity_received"] = ordered
        if payload.get("amount_received") is None and po.items:
            total = sum(
                (item.quantity or 0) * (item.price or 0) for item in po.items
            )
            if body.status == "completed":
                payload["amount_received"] = total

        svc = ReceivingService(uow, actor_id=auth.user_id)
        receipt = await svc.create_receipt(payload)
        data = await safe_validate(ReceiptResponse, receipt)
        await uow.commit()
        return ApiResponse(data=data, message="Receipt recorded")

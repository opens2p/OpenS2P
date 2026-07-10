"""
OpenS2P – Receiving API endpoints
===================================
"""
from __future__ import annotations
import uuid
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.schemas.common import ApiResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.schemas.serialization import safe_validate
from app.services.numbering import next_document_number
from app.models.receiving import Receipt

router = APIRouter(prefix="/receiving", tags=["Receiving"])


class ReceiptResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    receipt_number: str | None = None
    po_id: uuid.UUID
    status: str | None = None
    received_date: date | None = None
    tenant_id: uuid.UUID
    created_at: datetime | None = None


class ReceiptCreate(BaseModel):
    po_id: uuid.UUID
    status: str = "completed"


@router.get("/receipts", response_model=ApiResponse[list[ReceiptResponse]])
async def list_receipts(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        receipts = await uow.receipts.list()
        return ApiResponse(data=[await safe_validate(ReceiptResponse, r) for r in receipts])


@router.post("/receipts", response_model=ApiResponse[ReceiptResponse], status_code=201)
async def create_receipt(
    body: ReceiptCreate,
    _: None = Depends(require_permission(perm.PO_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        po = await uow.purchase_orders.get(body.po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        receipt_number = await next_document_number(
            uow.session, Receipt, "receipt_number", "GR",
        )
        receipt = await uow.receipts.create({
            "receipt_number": receipt_number,
            "po_id": body.po_id,
            "status": body.status,
            "received_date": date.today(),
        })
        data = await safe_validate(ReceiptResponse, receipt)
        await uow.commit()
        return ApiResponse(data=data, message="Receipt recorded")

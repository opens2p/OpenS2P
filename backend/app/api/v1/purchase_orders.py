"""
OpenS2P – Purchase Order API endpoints
========================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
)
from app.services.purchase_order_service import PurchaseOrderService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/purchase-orders", tags=["Procurement"])


@router.get("", response_model=ApiResponse[list[PurchaseOrderResponse]])
async def list_pos(
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        pos = await uow.purchase_orders.list(skip=skip, limit=limit)
        return ApiResponse(data=[PurchaseOrderResponse.model_validate(po) for po in pos])


@router.get("/{po_id}", response_model=ApiResponse[PurchaseOrderResponse])
async def get_po(
    po_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        po = await uow.purchase_orders.get_with_items(po_id)
        if po is None:
            raise HTTPException(status_code=404, detail="PO not found")
        return ApiResponse(data=PurchaseOrderResponse.model_validate(po))


@router.post("", response_model=ApiResponse[PurchaseOrderResponse], status_code=201)
async def create_po(
    body: PurchaseOrderCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow)
        po = await svc.create_po(body.model_dump(exclude_none=True))
        for item in body.items:
            await uow.purchase_order_items.create({
                "po_id": po.id,
                **item.model_dump(exclude_none=True),
            })
        await uow.commit()
        return ApiResponse(data=PurchaseOrderResponse.model_validate(po), message="PO created")


@router.post("/{po_id}/send", response_model=ApiResponse[PurchaseOrderResponse])
async def send_po(
    po_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow)
        result = await svc.send_to_supplier(po_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PO not found")
        await uow.commit()
        return ApiResponse(data=PurchaseOrderResponse.model_validate(result), message="PO sent")


@router.post("/{po_id}/close", response_model=ApiResponse[PurchaseOrderResponse])
async def close_po(
    po_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow)
        result = await svc.close_po(po_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PO not found")
        await uow.commit()
        return ApiResponse(data=PurchaseOrderResponse.model_validate(result), message="PO closed")

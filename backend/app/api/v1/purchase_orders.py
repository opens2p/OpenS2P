"""
OpenS2P – Purchase Order API endpoints
========================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.common import ApiResponse
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from app.schemas.serialization import safe_validate
from app.services.purchase_order_service import PurchaseOrderService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/purchase-orders", tags=["Procurement"])


@router.get("", response_model=ApiResponse[list[PurchaseOrderResponse]])
async def list_pos(
    _: AuthContext = Depends(require_permission(perm.PO_VIEW)),
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        pos = await uow.purchase_orders.list(
            skip=skip, limit=limit, with_items=True,
        )
        validated = [await safe_validate(PurchaseOrderResponse, po) for po in pos]
        return ApiResponse(data=validated)


@router.get("/{po_id}", response_model=ApiResponse[PurchaseOrderResponse])
async def get_po(
    po_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.PO_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        po = await uow.purchase_orders.get_with_items(po_id)
        if po is None:
            raise HTTPException(status_code=404, detail="PO not found")
        data = await safe_validate(PurchaseOrderResponse, po)
        return ApiResponse(data=data)


@router.post("", response_model=ApiResponse[PurchaseOrderResponse], status_code=201)
async def create_po(
    body: PurchaseOrderCreate,
    _: None = Depends(require_permission(perm.PO_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow, actor_id=auth.user_id)
        po = await svc.create_po(body.model_dump(exclude_none=True))
        for item in body.items:
            await uow.purchase_order_items.create({
                "po_id": po.id,
                **item.model_dump(exclude_none=True),
            })
        data = await safe_validate(PurchaseOrderResponse, po)
        resp = ApiResponse(data=data, message="PO created")
        await uow.commit()
        return resp


@router.patch("/{po_id}", response_model=ApiResponse[PurchaseOrderResponse])
async def update_po(
    po_id: uuid.UUID,
    body: PurchaseOrderUpdate,
    _: None = Depends(require_permission(perm.PO_UPDATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow, actor_id=auth.user_id)
        po = await uow.purchase_orders.update(
            po_id, body.model_dump(exclude_none=True),
        )
        if po is None:
            raise HTTPException(status_code=404, detail="PO not found")
        data = await safe_validate(PurchaseOrderResponse, po)
        resp = ApiResponse(data=data)
        await uow.commit()
        return resp


@router.post("/{po_id}/send", response_model=ApiResponse[PurchaseOrderResponse])
async def send_po(
    po_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PO_SEND)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow, actor_id=auth.user_id)
        result = await svc.send_to_supplier(po_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PO not found")
        data = await safe_validate(PurchaseOrderResponse, result)
        resp = ApiResponse(data=data, message="PO sent")
        await uow.commit()
        return resp


@router.post("/{po_id}/close", response_model=ApiResponse[PurchaseOrderResponse])
async def close_po(
    po_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PO_CLOSE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseOrderService(uow, actor_id=auth.user_id)
        result = await svc.close_po(po_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PO not found")
        data = await safe_validate(PurchaseOrderResponse, result)
        resp = ApiResponse(data=data, message="PO closed")
        await uow.commit()
        return resp


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_po(
    po_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PO_DELETE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Soft-delete a purchase order (sets is_active=False)."""
    async with uow:
        svc = PurchaseOrderService(uow, actor_id=auth.user_id)
        deleted = await svc.delete_po(po_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="PO not found")
        await uow.commit()

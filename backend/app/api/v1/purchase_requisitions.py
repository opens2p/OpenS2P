"""
OpenS2P – Purchase Requisition API endpoints
==============================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.purchase_order import PurchaseOrderResponse
from app.schemas.purchase_requisition import (
    PurchaseRequisitionCreate,
    PurchaseRequisitionResponse,
    PurchaseRequisitionUpdate,
)
from app.schemas.serialization import safe_validate
from app.services.purchase_requisition_service import (
    PurchaseRequisitionError,
    PurchaseRequisitionService,
    SupplierRequiredError,
)
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/purchase-requisitions", tags=["Procurement"])


@router.get("", response_model=ApiResponse[list[PurchaseRequisitionResponse]])
async def list_prs(
    _: AuthContext = Depends(require_permission(perm.PR_VIEW)),
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        prs = await uow.purchase_requisitions.list(skip=skip, limit=limit)
        return ApiResponse(data=[await safe_validate(PurchaseRequisitionResponse, pr) for pr in prs])


@router.get("/{pr_id}", response_model=ApiResponse[PurchaseRequisitionResponse])
async def get_pr(
    pr_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.PR_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        pr = await uow.purchase_requisitions.get_with_items(pr_id)
        if pr is None:
            raise HTTPException(status_code=404, detail="PR not found")
        return ApiResponse(data=await safe_validate(PurchaseRequisitionResponse, pr))


@router.post("", response_model=ApiResponse[PurchaseRequisitionResponse], status_code=201)
async def create_pr(
    body: PurchaseRequisitionCreate,
    _: None = Depends(require_permission(perm.PR_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow, actor_id=auth.user_id)
        pr_data = body.model_dump(exclude_none=True)
        items_data = pr_data.pop("items", [])
        pr = await svc.submit_pr(pr_data)
        # Create items if provided
        for item in items_data:
            await uow.purchase_requisition_items.create({
                "requisition_id": pr.id,
                **item,
            })
        data = await safe_validate(PurchaseRequisitionResponse, pr)
        resp = ApiResponse(data=data, message="PR created")
        await uow.commit()
        return resp


@router.patch("/{pr_id}", response_model=ApiResponse[PurchaseRequisitionResponse])
async def update_pr(
    pr_id: uuid.UUID,
    body: PurchaseRequisitionUpdate,
    _: None = Depends(require_permission(perm.PR_UPDATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow, actor_id=auth.user_id)
        pr = await uow.purchase_requisitions.update(
            pr_id, body.model_dump(exclude_none=True),
        )
        if pr is None:
            raise HTTPException(status_code=404, detail="PR not found")
        pr = await uow.purchase_requisitions.get_with_items(pr_id)
        data = await safe_validate(PurchaseRequisitionResponse, pr)
        resp = ApiResponse(data=data)
        await uow.commit()
        return resp


@router.post("/{pr_id}/approve", response_model=ApiResponse[PurchaseRequisitionResponse])
async def approve_pr(
    pr_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PR_APPROVE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow, actor_id=auth.user_id)
        try:
            result = await svc.approve_pr(pr_id)
        except SupplierRequiredError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PurchaseRequisitionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if result is None:
            raise HTTPException(status_code=404, detail="PR not found")
        data = await safe_validate(PurchaseRequisitionResponse, result)
        resp = ApiResponse(data=data, message="PR approved and PO created")
        await uow.commit()
        return resp


@router.post("/{pr_id}/create-po", response_model=ApiResponse[PurchaseOrderResponse])
async def create_po_from_pr(
    pr_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PO_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Create a purchase order from an approved requisition."""
    async with uow:
        svc = PurchaseRequisitionService(uow, actor_id=auth.user_id)
        try:
            po = await svc.create_po_from_pr(pr_id)
        except SupplierRequiredError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PurchaseRequisitionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if po is None:
            raise HTTPException(status_code=404, detail="PR not found")
        data = await safe_validate(PurchaseOrderResponse, po)
        resp = ApiResponse(data=data, message="PO created from requisition")
        await uow.commit()
        return resp


@router.post("/{pr_id}/reject", response_model=ApiResponse[PurchaseRequisitionResponse])
async def reject_pr(
    pr_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PR_REJECT)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow, actor_id=auth.user_id)
        result = await svc.reject_pr(pr_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PR not found")
        data = await safe_validate(PurchaseRequisitionResponse, result)
        resp = ApiResponse(data=data, message="PR rejected")
        await uow.commit()
        return resp


@router.delete("/{pr_id}", status_code=204)
async def delete_pr(
    pr_id: uuid.UUID,
    _: None = Depends(require_permission(perm.PR_DELETE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Soft-delete a purchase requisition (sets is_active=False)."""
    async with uow:
        svc = PurchaseRequisitionService(uow, actor_id=auth.user_id)
        deleted = await svc.delete_pr(pr_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="PR not found")
        await uow.commit()

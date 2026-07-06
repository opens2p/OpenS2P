"""
OpenS2P – Purchase Requisition API endpoints
==============================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.purchase_requisition import (
    PurchaseRequisitionCreate,
    PurchaseRequisitionResponse,
)
from app.services.purchase_requisition_service import PurchaseRequisitionService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/purchase-requisitions", tags=["Procurement"])


@router.get("", response_model=ApiResponse[list[PurchaseRequisitionResponse]])
async def list_prs(
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        prs = await uow.purchase_requisitions.list(skip=skip, limit=limit)
        return ApiResponse(data=[PurchaseRequisitionResponse.model_validate(pr) for pr in prs])


@router.get("/{pr_id}", response_model=ApiResponse[PurchaseRequisitionResponse])
async def get_pr(
    pr_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        pr = await uow.purchase_requisitions.get_with_items(pr_id)
        if pr is None:
            raise HTTPException(status_code=404, detail="PR not found")
        return ApiResponse(data=PurchaseRequisitionResponse.model_validate(pr))


@router.post("", response_model=ApiResponse[PurchaseRequisitionResponse], status_code=201)
async def create_pr(
    body: PurchaseRequisitionCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow)
        pr = await svc.submit_pr(body.model_dump(exclude_none=True))
        # Create items if provided
        for item in body.items:
            await uow.purchase_requisition_items.create({
                "requisition_id": pr.id,
                **item.model_dump(exclude_none=True),
            })
        await uow.commit()
        return ApiResponse(data=PurchaseRequisitionResponse.model_validate(pr), message="PR created")


@router.post("/{pr_id}/approve", response_model=ApiResponse[PurchaseRequisitionResponse])
async def approve_pr(
    pr_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow)
        result = await svc.approve_pr(pr_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PR not found")
        await uow.commit()
        return ApiResponse(data=PurchaseRequisitionResponse.model_validate(result), message="PR approved")


@router.post("/{pr_id}/reject", response_model=ApiResponse[PurchaseRequisitionResponse])
async def reject_pr(
    pr_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = PurchaseRequisitionService(uow)
        result = await svc.reject_pr(pr_id)
        if result is None:
            raise HTTPException(status_code=404, detail="PR not found")
        await uow.commit()
        return ApiResponse(data=PurchaseRequisitionResponse.model_validate(result), message="PR rejected")

"""
OpenS2P – Supplier API endpoints
=================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.common import ApiResponse
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierSummary,
    SupplierUpdate,
)
from app.services.supplier_service import SupplierService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/suppliers", tags=["Supplier Management"])


@router.get("", response_model=ApiResponse[list[SupplierSummary]])
async def list_suppliers(
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        suppliers = await svc.uow.suppliers.list(skip=skip, limit=limit)
        return ApiResponse(data=[SupplierSummary.model_validate(s) for s in suppliers])


@router.get("/{supplier_id}", response_model=ApiResponse[SupplierResponse])
async def get_supplier(
    supplier_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        supplier = await svc.uow.suppliers.get(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return ApiResponse(data=SupplierResponse.model_validate(supplier))


@router.post("", response_model=ApiResponse[SupplierResponse], status_code=201)
async def create_supplier(
    body: SupplierCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        supplier = await svc.onboard_supplier(body.model_dump(exclude_none=True))
        await uow.commit()
        return ApiResponse(
            data=SupplierResponse.model_validate(supplier),
            message="Supplier created",
        )


@router.patch("/{supplier_id}", response_model=ApiResponse[SupplierResponse])
async def update_supplier(
    supplier_id: uuid.UUID,
    body: SupplierUpdate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        supplier = await svc.uow.suppliers.update(
            supplier_id, body.model_dump(exclude_none=True),
        )
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        await uow.commit()
        return ApiResponse(data=SupplierResponse.model_validate(supplier))


@router.post("/{supplier_id}/approve", response_model=ApiResponse[SupplierResponse])
async def approve_supplier(
    supplier_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        result = await svc.approve_supplier(supplier_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        await uow.commit()
        return ApiResponse(
            data=SupplierResponse.model_validate(result),
            message="Supplier approved",
        )


@router.post("/{supplier_id}/block", response_model=ApiResponse[SupplierResponse])
async def block_supplier(
    supplier_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        result = await svc.block_supplier(supplier_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        await uow.commit()
        return ApiResponse(
            data=SupplierResponse.model_validate(result),
            message="Supplier blocked",
        )

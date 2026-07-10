"""
OpenS2P – Supplier API endpoints
=================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.common import ApiResponse
from app.schemas.serialization import safe_validate
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierSummary,
    SupplierUpdate,
)
from app.services.supplier_service import SupplierService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/suppliers", tags=["Supplier Management"])


@router.get("", response_model=ApiResponse[list[SupplierSummary]])
async def list_suppliers(
    _: AuthContext = Depends(require_permission(perm.SUPPLIER_VIEW)),
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        suppliers = await svc.uow.suppliers.list(skip=skip, limit=limit)
        return ApiResponse(data=[await safe_validate(SupplierSummary, s) for s in suppliers])


@router.get("/{supplier_id}", response_model=ApiResponse[SupplierResponse])
async def get_supplier(
    supplier_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.SUPPLIER_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow)
        supplier = await svc.uow.suppliers.get(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return ApiResponse(data=await safe_validate(SupplierResponse, supplier))


@router.post("", response_model=ApiResponse[SupplierResponse], status_code=201)
async def create_supplier(
    body: SupplierCreate,
    _: None = Depends(require_permission(perm.SUPPLIER_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow, actor_id=auth.user_id)
        supplier = await svc.onboard_supplier(body.model_dump(exclude_none=True))
        data = await safe_validate(SupplierResponse, supplier)
        resp = ApiResponse(data=data, message="Supplier created")
        await uow.commit()
        return resp


@router.patch("/{supplier_id}", response_model=ApiResponse[SupplierResponse])
async def update_supplier(
    supplier_id: uuid.UUID,
    body: SupplierUpdate,
    _: None = Depends(require_permission(perm.SUPPLIER_UPDATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow, actor_id=auth.user_id)
        supplier = await svc.uow.suppliers.update(
            supplier_id, body.model_dump(exclude_none=True),
        )
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        data = await safe_validate(SupplierResponse, supplier)
        resp = ApiResponse(data=data)
        await uow.commit()
        return resp


@router.post("/{supplier_id}/approve", response_model=ApiResponse[SupplierResponse])
async def approve_supplier(
    supplier_id: uuid.UUID,
    _: None = Depends(require_permission(perm.SUPPLIER_APPROVE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow, actor_id=auth.user_id)
        result = await svc.approve_supplier(supplier_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        data = await safe_validate(SupplierResponse, result)
        resp = ApiResponse(data=data, message="Supplier approved")
        await uow.commit()
        return resp


@router.post("/{supplier_id}/block", response_model=ApiResponse[SupplierResponse])
async def block_supplier(
    supplier_id: uuid.UUID,
    _: None = Depends(require_permission(perm.SUPPLIER_BLOCK)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SupplierService(uow, actor_id=auth.user_id)
        result = await svc.block_supplier(supplier_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        data = await safe_validate(SupplierResponse, result)
        resp = ApiResponse(data=data, message="Supplier blocked")
        await uow.commit()
        return resp


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: uuid.UUID,
    _: None = Depends(require_permission(perm.SUPPLIER_DELETE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Soft-delete a supplier (sets is_active=False)."""
    async with uow:
        svc = SupplierService(uow, actor_id=auth.user_id)
        deleted = await svc.delete_supplier(supplier_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Supplier not found")
        await uow.commit()

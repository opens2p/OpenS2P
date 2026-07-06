"""
OpenS2P – Admin API endpoints
===============================
Health check, tenant info, and administrative operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.common import ApiResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OpenS2P API", "version": "0.1.0"}


@router.get("/stats")
async def tenant_stats(uow: UnitOfWork = Depends(get_unit_of_work)):
    async with uow:
        return ApiResponse(data={
            "suppliers": await uow.suppliers.count(),
            "contracts": await uow.contracts.count(),
            "purchase_orders": await uow.purchase_orders.count(),
            "invoices": await uow.invoices.count(),
            "users": await uow.users.count(),
        })

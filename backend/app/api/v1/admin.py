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
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/health")
async def health_check(
    _: AuthContext = Depends(require_permission(perm.ADMIN_HEALTH)),
):
    return {"status": "healthy", "service": "OpenS2P API", "version": "0.1.0"}


@router.get("/stats")
async def tenant_stats(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        return ApiResponse(data={
            "suppliers": await uow.suppliers.count(),
            "contracts": await uow.contracts.count(),
            "purchase_orders": await uow.purchase_orders.count(),
            "invoices": await uow.invoices.count(),
            "users": await uow.users.count(),
        })

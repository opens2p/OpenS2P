"""
OpenS2P – V1 API Router
========================
Aggregates all domain endpoint modules under the ``/api/v1`` prefix.
"""

from fastapi import APIRouter

from . import (
    auth,
    suppliers,
    contracts,
    sourcing,
    purchase_requisitions,
    purchase_orders,
    invoices,
    workflows,
    audit,
    ai,
    admin,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(suppliers.router)
router.include_router(contracts.router)
router.include_router(sourcing.router)
router.include_router(purchase_requisitions.router)
router.include_router(purchase_orders.router)
router.include_router(invoices.router)
router.include_router(workflows.router)
router.include_router(audit.router)
router.include_router(ai.router)
router.include_router(admin.router)

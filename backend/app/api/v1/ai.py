"""
OpenS2P – AI API endpoints
============================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.schemas.common import ApiResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.ai import SupplierAIService, ContractAIService, InvoiceAIService

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


@router.get("/supplier/{supplier_id}/analyze")
async def analyze_supplier(
    supplier_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI risk analysis for a supplier."""
    async with uow:
        svc = SupplierAIService(uow)
        result = await svc.analyze_risk(supplier_id)
        return ApiResponse(data=result)


@router.get("/supplier/{supplier_id}/recommend-category")
async def recommend_supplier_category(
    supplier_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI category recommendations for a supplier."""
    async with uow:
        svc = SupplierAIService(uow)
        result = await svc.recommend_category(supplier_id)
        return ApiResponse(data=result)


@router.get("/contract/{contract_id}/review")
async def review_contract(
    contract_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI contract clause risk review."""
    async with uow:
        svc = ContractAIService(uow)
        result = await svc.review(contract_id)
        return ApiResponse(data=result)


@router.get("/contract/{contract_id}/suggest-renewal")
async def suggest_renewal(
    contract_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI-suggested renewal terms for a contract."""
    async with uow:
        svc = ContractAIService(uow)
        result = await svc.suggest_renewal_terms(contract_id)
        return ApiResponse(data=result)


@router.get("/invoice/{invoice_id}/analyze")
async def analyze_invoice(
    invoice_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI anomaly and fraud analysis for an invoice."""
    async with uow:
        svc = InvoiceAIService(uow)
        result = await svc.analyze(invoice_id)
        return ApiResponse(data=result)


@router.get("/invoice/{invoice_id}/detect-anomalies")
async def detect_invoice_anomalies(
    invoice_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI anomaly detection for an invoice."""
    async with uow:
        svc = InvoiceAIService(uow)
        result = await svc.detect_anomalies(invoice_id)
        return ApiResponse(data=result)


@router.get("/contract/{contract_id}/summarize")
async def summarize_contract(
    contract_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI contract summarization."""
    async with uow:
        svc = ContractAIService(uow)
        result = await svc.summarize(contract_id)
        return ApiResponse(data=result)


@router.get("/contract/{contract_id}/analyze-risk")
async def analyze_contract_risk(
    contract_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """AI contract risk analysis."""
    async with uow:
        svc = ContractAIService(uow)
        result = await svc.analyze_risk(contract_id)
        return ApiResponse(data=result)

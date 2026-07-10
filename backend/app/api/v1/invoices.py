"""
OpenS2P – Invoice API endpoints
=================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    MatchAction,
    PaymentApproval,
)
from app.schemas.serialization import safe_validate
from app.services.invoice_service import InvoiceService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/invoices", tags=["Invoice Management"])


@router.get("", response_model=ApiResponse[list[InvoiceResponse]])
async def list_invoices(
    _: AuthContext = Depends(require_permission(perm.INVOICE_VIEW)),
    skip: int = 0,
    limit: int = 50,
    exception_queue: bool = False,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow)
        if exception_queue:
            invoices = await svc.get_exception_queue()
        else:
            invoices = await uow.invoices.list(skip=skip, limit=limit)
        return ApiResponse(data=[await safe_validate(InvoiceResponse, i) for i in invoices])


@router.get("/{invoice_id}", response_model=ApiResponse[InvoiceResponse])
async def get_invoice(
    invoice_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.INVOICE_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        invoice = await uow.invoices.get(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return ApiResponse(data=await safe_validate(InvoiceResponse, invoice))


@router.post("", response_model=ApiResponse[InvoiceResponse], status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    _: None = Depends(require_permission(perm.INVOICE_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow, actor_id=auth.user_id)
        invoice = await svc.submit_invoice(body.model_dump(exclude_none=True))
        data = await safe_validate(InvoiceResponse, invoice)
        resp = ApiResponse(data=data, message="Invoice created")
        await uow.commit()
        return resp


@router.patch("/{invoice_id}", response_model=ApiResponse[InvoiceResponse])
async def update_invoice(
    invoice_id: uuid.UUID,
    body: InvoiceUpdate,
    _: None = Depends(require_permission(perm.INVOICE_UPDATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow, actor_id=auth.user_id)
        invoice = await uow.invoices.update(
            invoice_id, body.model_dump(exclude_none=True),
        )
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        data = await safe_validate(InvoiceResponse, invoice)
        resp = ApiResponse(data=data)
        await uow.commit()
        return resp


@router.post("/{invoice_id}/match", response_model=ApiResponse[InvoiceResponse])
async def match_invoice(
    invoice_id: uuid.UUID,
    _: None = Depends(require_permission(perm.INVOICE_MATCH)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow, actor_id=auth.user_id)
        result = await svc.perform_matching(invoice_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        data = await safe_validate(InvoiceResponse, result)
        resp = ApiResponse(data=data, message="Invoice matched")
        await uow.commit()
        return resp


@router.post("/{invoice_id}/approve", response_model=ApiResponse[InvoiceResponse])
async def approve_invoice(
    invoice_id: uuid.UUID,
    body: PaymentApproval,
    _: None = Depends(require_permission(perm.INVOICE_APPROVE_PAYMENT)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow, actor_id=auth.user_id)
        result = await svc.approve_payment(invoice_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        data = await safe_validate(InvoiceResponse, result)
        resp = ApiResponse(data=data, message="Payment approved")
        await uow.commit()
        return resp


@router.post("/{invoice_id}/pay", response_model=ApiResponse[InvoiceResponse])
async def pay_invoice(
    invoice_id: uuid.UUID,
    _: None = Depends(require_permission(perm.INVOICE_PAY)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow, actor_id=auth.user_id)
        result = await svc.approve_payment(invoice_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        data = await safe_validate(InvoiceResponse, result)
        resp = ApiResponse(data=data, message="Payment approved")
        await uow.commit()
        return resp


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: uuid.UUID,
    _: None = Depends(require_permission(perm.INVOICE_DELETE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Soft-delete an invoice (sets is_active=False)."""
    async with uow:
        svc = InvoiceService(uow, actor_id=auth.user_id)
        deleted = await svc.delete_invoice(invoice_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Invoice not found")
        await uow.commit()

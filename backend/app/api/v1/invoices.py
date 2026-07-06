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
    MatchAction,
    PaymentApproval,
)
from app.services.invoice_service import InvoiceService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/invoices", tags=["Invoice Management"])


@router.get("", response_model=ApiResponse[list[InvoiceResponse]])
async def list_invoices(
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
        return ApiResponse(data=[InvoiceResponse.model_validate(i) for i in invoices])


@router.get("/{invoice_id}", response_model=ApiResponse[InvoiceResponse])
async def get_invoice(
    invoice_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        invoice = await uow.invoices.get(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return ApiResponse(data=InvoiceResponse.model_validate(invoice))


@router.post("", response_model=ApiResponse[InvoiceResponse], status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow)
        invoice = await svc.submit_invoice(body.model_dump(exclude_none=True))
        await uow.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(invoice), message="Invoice created")


@router.post("/{invoice_id}/match", response_model=ApiResponse[InvoiceResponse])
async def match_invoice(
    invoice_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow)
        result = await svc.perform_matching(invoice_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        await uow.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(result), message="Invoice matched")


@router.post("/{invoice_id}/approve", response_model=ApiResponse[InvoiceResponse])
async def approve_invoice(
    invoice_id: uuid.UUID,
    body: PaymentApproval,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = InvoiceService(uow)
        result = await svc.approve_payment(invoice_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        await uow.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(result), message="Payment approved")

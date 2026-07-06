"""
OpenS2P – Sourcing API endpoints
==================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.sourcing import (
    SourcingEventCreate,
    SourcingEventResponse,
    BidCreate,
    BidResponse,
    AwardRequest,
)
from app.services.sourcing_service import SourcingService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/sourcing", tags=["Sourcing"])


@router.get("/events", response_model=ApiResponse[list[SourcingEventResponse]])
async def list_events(
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        events = await uow.sourcing_events.list(skip=skip, limit=limit)
        return ApiResponse(data=[SourcingEventResponse.model_validate(e) for e in events])


@router.get("/events/{event_id}", response_model=ApiResponse[SourcingEventResponse])
async def get_event(
    event_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        event = await uow.sourcing_events.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return ApiResponse(data=SourcingEventResponse.model_validate(event))


@router.post("/events", response_model=ApiResponse[SourcingEventResponse], status_code=201)
async def create_event(
    body: SourcingEventCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SourcingService(uow)
        event = await svc.create_event(body.model_dump(exclude_none=True))
        await uow.commit()
        return ApiResponse(data=SourcingEventResponse.model_validate(event), message="Event created")


@router.get("/events/{event_id}/bids", response_model=ApiResponse[list[BidResponse]])
async def list_bids(
    event_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        bids = await uow.supplier_bids.list_by_event(event_id)
        return ApiResponse(data=[BidResponse.model_validate(b) for b in bids])


@router.post("/events/{event_id}/bids", response_model=ApiResponse[BidResponse], status_code=201)
async def submit_bid(
    event_id: uuid.UUID,
    body: BidCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SourcingService(uow)
        bid = await svc.receive_bid(
            event_id=event_id,
            supplier_id=body.supplier_id,
            bid_amount=body.bid_amount,
            extras=body.extras,
        )
        await uow.commit()
        return ApiResponse(data=BidResponse.model_validate(bid), message="Bid submitted")


@router.post("/events/{event_id}/award", response_model=ApiResponse[SourcingEventResponse])
async def award_event(
    event_id: uuid.UUID,
    body: AwardRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SourcingService(uow)
        result = await svc.award_supplier(event_id, body.supplier_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Event not found")
        await uow.commit()
        return ApiResponse(data=SourcingEventResponse.model_validate(result), message="Supplier awarded")

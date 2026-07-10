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
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/sourcing", tags=["Sourcing"])


@router.get("/events", response_model=ApiResponse[list[SourcingEventResponse]])
async def list_events(
    _: AuthContext = Depends(require_permission(perm.SOURCING_VIEW)),
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
    _: AuthContext = Depends(require_permission(perm.SOURCING_VIEW)),
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
    _: None = Depends(require_permission(perm.SOURCING_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SourcingService(uow, actor_id=auth.user_id)
        event = await svc.create_event(body.model_dump(exclude_none=True))
        await uow.commit()
        return ApiResponse(data=SourcingEventResponse.model_validate(event), message="Event created")


@router.get("/events/{event_id}/bids", response_model=ApiResponse[list[BidResponse]])
async def list_bids(
    event_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.SOURCING_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        bids = await uow.supplier_bids.list_by_event(event_id)
        return ApiResponse(data=[BidResponse.model_validate(b) for b in bids])


@router.post("/events/{event_id}/bids", response_model=ApiResponse[BidResponse], status_code=201)
async def submit_bid(
    event_id: uuid.UUID,
    body: BidCreate,
    _: None = Depends(require_permission(perm.SOURCING_BID)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SourcingService(uow, actor_id=auth.user_id)
        bid = await svc.receive_bid(
            event_id=event_id,
            supplier_id=body.supplier_id,
            bid_amount=body.bid_amount,
            extras=body.extras,
        )
        await uow.commit()
        return ApiResponse(data=BidResponse.model_validate(bid), message="Bid submitted")


@router.post("/events/{event_id}/publish", response_model=ApiResponse[SourcingEventResponse])
async def publish_event(
    event_id: uuid.UUID,
    _: None = Depends(require_permission(perm.SOURCING_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Publish a sourcing event (make it visible to suppliers)."""
    async with uow:
        event = await uow.sourcing_events.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        # In production: notify suppliers, set open date
        await uow.commit()
        return ApiResponse(data=SourcingEventResponse.model_validate(event), message="Event published")


@router.get("/events/{event_id}/comparison", response_model=ApiResponse[dict])
async def compare_bids(
    event_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.SOURCING_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Compare all bids for a sourcing event."""
    async with uow:
        svc = SourcingService(uow)
        comparison = await svc.compare_bids(event_id)
        if comparison is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return ApiResponse(data=comparison)


@router.post("/events/{event_id}/award", response_model=ApiResponse[SourcingEventResponse])
async def award_event(
    event_id: uuid.UUID,
    body: AwardRequest,
    _: AuthContext = Depends(require_permission(perm.SOURCING_AWARD)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = SourcingService(uow, actor_id=auth.user_id)
        result = await svc.award_supplier(event_id, body.supplier_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Event not found")
        await uow.commit()
        return ApiResponse(data=SourcingEventResponse.model_validate(result), message="Supplier awarded")

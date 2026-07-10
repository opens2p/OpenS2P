"""
OpenS2P – Sourcing Service
===========================
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import SourcingEvent, SupplierBid
from app.services.uow import UnitOfWork


class SourcingService:
    """Sourcing event lifecycle operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def create_event(self, data: dict[str, Any]) -> SourcingEvent:
        event = await self.uow.sourcing_events.create(data)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="sourcing_event",
            entity_id=event.id,
            event_type="SOURCING_EVENT_CREATED",
            new_values=data,
            created_by=self.actor_id,
        )
        return event

    async def receive_bid(
        self,
        event_id: uuid.UUID,
        supplier_id: uuid.UUID,
        bid_amount: Decimal,
        extras: dict[str, Any] | None = None,
    ) -> SupplierBid:
        bid = await self.uow.supplier_bids.create({
            "event_id": event_id,
            "supplier_id": supplier_id,
            "bid_amount": bid_amount,
            "extras": extras,
        })
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="supplier_bid",
            entity_id=bid.id,
            event_type="BID_SUBMITTED",
            new_values={"event_id": str(event_id), "bid_amount": str(bid_amount)},
            created_by=self.actor_id,
        )
        return bid

    async def award_supplier(
        self,
        event_id: uuid.UUID,
        supplier_id: uuid.UUID,
    ) -> SourcingEvent | None:
        """Award a sourcing event to the winning supplier."""
        event = await self.uow.sourcing_events.get(event_id)
        if event is None:
            return None
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="sourcing_event",
            entity_id=event_id,
            event_type="SOURCING_EVENT_AWARDED",
            new_values={"awarded_supplier_id": str(supplier_id)},
            created_by=self.actor_id,
        )
        return event

    async def compare_bids(self, event_id: uuid.UUID) -> dict | None:
        """Compare all bids for an event, sorted by amount."""
        event = await self.uow.sourcing_events.get(event_id)
        if event is None:
            return None
        bids = await self.uow.supplier_bids.list_by_event(event_id)
        sorted_bids = sorted(bids, key=lambda b: b.bid_amount or 0)
        lowest = sorted_bids[0] if sorted_bids else None
        return {
            "event_id": str(event_id),
            "total_bids": len(sorted_bids),
            "lowest_bid": float(lowest.bid_amount) if lowest and lowest.bid_amount else 0,
            "highest_bid": float(sorted_bids[-1].bid_amount) if sorted_bids and sorted_bids[-1].bid_amount else 0,
            "average_bid": round(sum(float(b.bid_amount or 0) for b in sorted_bids) / len(sorted_bids), 2) if sorted_bids else 0,
            "bids": [
                {"supplier_id": str(b.supplier_id), "amount": float(b.bid_amount or 0), "submitted_at": b.submitted_at.isoformat() if b.submitted_at else None}
                for b in sorted_bids
            ],
        }

    async def get_lowest_bidder(
        self,
        event_id: uuid.UUID,
    ) -> SupplierBid | None:
        return await self.uow.supplier_bids.get_lowest_bid(event_id)

"""
OpenS2P – In-Process Event Bus
================================
Simple in-process event bus for domain events.
In production, replace with Redis pub/sub or a message queue.

Usage::

    from app.events.event_bus import publish, subscribe

    async def handle_workflow_started(event):
        print(f"Workflow started: {event}")

    subscribe("WORKFLOW_STARTED", handle_workflow_started)
    await publish("WORKFLOW_STARTED", {"workflow_id": "..."})
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

# Event type constants
WORKFLOW_STARTED = "WORKFLOW_STARTED"
WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
WORKFLOW_REJECTED = "WORKFLOW_REJECTED"
SUPPLIER_CREATED = "SUPPLIER_CREATED"
SUPPLIER_APPROVED = "SUPPLIER_APPROVED"
CONTRACT_ACTIVATED = "CONTRACT_ACTIVATED"
PR_APPROVED = "PR_APPROVED"
PO_CREATED = "PO_CREATED"
INVOICE_MATCHED = "INVOICE_MATCHED"
INVOICE_PAID = "INVOICE_PAID"

Handler = Callable[..., Coroutine[Any, Any, None]]

_handlers: dict[str, list[Handler]] = {}


def subscribe(event_type: str, handler: Handler) -> None:
    """Register a handler for an event type."""
    if event_type not in _handlers:
        _handlers[event_type] = []
    _handlers[event_type].append(handler)


def unsubscribe(event_type: str, handler: Handler) -> None:
    """Remove a handler for an event type."""
    if event_type in _handlers:
        _handlers[event_type].remove(handler)


async def publish(event_type: str, payload: dict[str, Any]) -> None:
    """Publish an event to all registered handlers."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    handlers = _handlers.get(event_type, [])
    for handler in handlers:
        try:
            await handler(event)
        except Exception as e:
            print(f"Event handler error for {event_type}: {e}")


def clear_handlers() -> None:
    """Clear all registered handlers (useful for testing)."""
    _handlers.clear()

"""
Analytics event handlers — update KPI snapshots when domain events occur.
"""
from __future__ import annotations
from app.events.event_bus import subscribe, publish
from app.events import schemas as events


async def on_invoice_matched(event: dict) -> None:
    """Update invoice match rate KPI when an invoice is matched."""
    pass  # Simplified — in production, update KPI snapshot table


async def on_workflow_completed(event: dict) -> None:
    """Update cycle time KPI when a workflow completes."""
    pass


def register_analytics_handlers() -> None:
    """Register all analytics event handlers."""
    subscribe(events.INVOICE_MATCHED, on_invoice_matched)
    subscribe(events.WORKFLOW_COMPLETED, on_workflow_completed)

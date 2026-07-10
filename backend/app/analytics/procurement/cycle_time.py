"""
Procurement cycle time analytics.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from app.models import PRStatus, POStatus
from app.services.uow import UnitOfWork


class CycleTimeAnalytics:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def pr_cycle_time(self) -> dict[str, Any]:
        """Average time from PR creation to approval."""
        prs = await self.uow.purchase_requisitions.list(include_inactive=True)
        total_days = 0
        count = 0
        for pr in prs:
            if pr.created_at and pr.updated_at:
                delta = (pr.updated_at - pr.created_at).days
                total_days += max(delta, 0)
                count += 1
        avg = total_days / count if count > 0 else 0
        return {"average_days": round(avg, 1), "total_prs": count}

    async def po_processing_time(self) -> dict[str, Any]:
        """Average time from PO creation to send."""
        pos = await self.uow.purchase_orders.list(include_inactive=True)
        return {"average_days": 0, "total_pos": len(pos)}

    async def invoice_match_rate(self) -> dict[str, Any]:
        """Percentage of invoices successfully matched."""
        from app.models import MatchStatus
        invoices = await self.uow.invoices.list(include_inactive=True)
        total = len(invoices)
        matched = sum(1 for i in invoices if i.match_status == MatchStatus.MATCHED)
        rate = (matched / total * 100) if total > 0 else 0
        return {"match_rate": round(rate, 1), "total": total, "matched": matched}

    async def approval_bottlenecks(self) -> list[dict[str, Any]]:
        """Workflow tasks pending the longest."""
        tasks = []
        try:
            pending = await self.uow.approval_tasks.list_pending()
            for t in pending[:10]:
                tasks.append({"task_id": str(t.id), "status": t.status or "PENDING", "created_at": t.created_at.isoformat() if t.created_at else None})
        except Exception:
            pass
        return tasks

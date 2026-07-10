"""
Dashboard aggregation service — combines all KPIs into dashboard responses.
"""
from __future__ import annotations
from typing import Any
from app.services.uow import UnitOfWork
from app.analytics.spend.service import SpendAnalytics
from app.analytics.supplier.scorecard import SupplierScorecard
from app.analytics.procurement.cycle_time import CycleTimeAnalytics
from app.analytics.contracts.compliance import ContractAnalytics
from app.analytics.kpi_engine import calculate_trend


async def get_executive_dashboard(uow: UnitOfWork) -> dict[str, Any]:
    spend = SpendAnalytics(uow)
    suppliers = SupplierScorecard(uow)
    cycle = CycleTimeAnalytics(uow)
    contracts = ContractAnalytics(uow)

    total_spend = await spend.total_spend()

    return {
        "kpi_summary": {
            "total_spend": float(total_spend),
            "total_suppliers": await suppliers.supplier_count(),
            "active_contracts": await contracts.active_contracts(),
            "pending_approvals": 0,
            "invoice_match_rate": (await cycle.invoice_match_rate())["match_rate"],
        },
        "spend": {
            "total": float(total_spend),
            "by_supplier": await spend.spend_by_supplier(),
            "by_category": await spend.spend_by_category(),
            "trend": await spend.monthly_spend_trend(),
        },
        "suppliers": await suppliers.scorecard(),
        "cycle_times": {
            "pr_cycle_time": await cycle.pr_cycle_time(),
            "invoice_match_rate": await cycle.invoice_match_rate(),
        },
        "contracts": {
            "active": await contracts.active_contracts(),
            "expiring": await contracts.expiring_contracts(),
            "total_value": await contracts.total_contract_value(),
        },
    }


async def get_spend_dashboard(uow: UnitOfWork) -> dict[str, Any]:
    spend = SpendAnalytics(uow)
    return {
        "total_spend": float(await spend.total_spend()),
        "by_supplier": await spend.spend_by_supplier(),
        "by_category": await spend.spend_by_category(),
        "trend": await spend.monthly_spend_trend(),
        "maverick": await spend.maverick_spend(),
    }

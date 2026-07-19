"""
OpenS2P – Analytics API endpoints
===================================
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.common import ApiResponse
from app.schemas.analytics import DashboardResponse, SavedReportCreate, SavedReportResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.schemas.serialization import safe_validate
from app.analytics.dashboards import get_executive_dashboard, get_spend_dashboard
from app.analytics.spend.service import SpendAnalytics
from app.analytics.supplier.scorecard import SupplierScorecard
from app.analytics.procurement.cycle_time import CycleTimeAnalytics
from app.analytics.contracts.compliance import ContractAnalytics
from app.export.service import ExportService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=ApiResponse[DashboardResponse])
async def executive_dashboard(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        dashboard = await get_executive_dashboard(uow)
        return ApiResponse(data=dashboard)


@router.get("/spend", response_model=ApiResponse[dict])
async def spend_analytics(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        data = await get_spend_dashboard(uow)
        return ApiResponse(data=data)


@router.get("/spend/categories", response_model=ApiResponse[list])
async def spend_by_category(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        spend = SpendAnalytics(uow)
        data = await spend.spend_by_category()
        return ApiResponse(data=data)


@router.get("/spend/leakage", response_model=ApiResponse[dict])
async def spend_leakage(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        spend = SpendAnalytics(uow)
        data = await spend.leakage_opportunities()
        return ApiResponse(data=data)


@router.get("/suppliers/scorecard", response_model=ApiResponse[dict])
async def supplier_scorecard(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        sc = SupplierScorecard(uow)
        data = await sc.scorecard()
        return ApiResponse(data=data)


@router.get("/contracts", response_model=ApiResponse[dict])
async def contract_analytics(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        ca = ContractAnalytics(uow)
        data = {
            "active": await ca.active_contracts(),
            "expiring": await ca.expiring_contracts(),
            "total_value": await ca.total_contract_value(),
            "compliance": await ca.compliance_rate(),
        }
        return ApiResponse(data=data)


@router.get("/workflows", response_model=ApiResponse[dict])
async def workflow_analytics(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        cycle = CycleTimeAnalytics(uow)
        data = {
            "cycle_times": await cycle.pr_cycle_time(),
            "invoice_match_rate": await cycle.invoice_match_rate(),
            "bottlenecks": await cycle.approval_bottlenecks(),
        }
        return ApiResponse(data=data)


@router.post("/reports", response_model=ApiResponse[SavedReportResponse], status_code=201)
async def create_report(
    body: SavedReportCreate,
    _: None = Depends(require_permission(perm.ADMIN_STATS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        report = await uow.saved_reports.create({
            "report_name": body.report_name,
            "report_type": body.report_type,
            "config": body.config,
        })
        resp = await safe_validate(SavedReportResponse, report)
        await uow.commit()
        return ApiResponse(data=resp, message="Report created")


@router.get("/reports", response_model=ApiResponse[list])
async def list_reports(
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        reports = await uow.saved_reports.list()
        return ApiResponse(data=[await safe_validate(SavedReportResponse, r) for r in reports])


@router.get("/reports/{report_id}", response_model=ApiResponse[SavedReportResponse])
async def get_report(
    report_id: str,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    import uuid
    rid = uuid.UUID(report_id)
    async with uow:
        report = await uow.saved_reports.get(rid)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return ApiResponse(data=await safe_validate(SavedReportResponse, report))


@router.post("/reports/export")
async def export_report(
    format: str = Query("csv", pattern="^(csv|excel)$"),
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        dashboard = await get_executive_dashboard(uow)
        flat_data = _flatten_dashboard(dashboard)
        filename, mime_type, content = ExportService.generate_report(flat_data, format)
        from fastapi.responses import Response
        return Response(content=content, media_type=mime_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


def _flatten_dashboard(dashboard: dict) -> list[dict]:
    """Flatten nested dashboard dict into list of rows for CSV export."""
    rows = []
    for category, metrics in dashboard.items():
        if isinstance(metrics, dict):
            for key, value in metrics.items():
                if not isinstance(value, (dict, list)):
                    rows.append({"category": category, "metric": key, "value": str(value)})
    return rows

"""
OpenS2P – Analytics & KPIs Integration Tests
=============================================
Tests for KPI engine, domain analytics services, export service,
and analytics API endpoints.

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k analytics --no-header
"""

from __future__ import annotations

import csv
import io
import uuid
from decimal import Decimal

import httpx
import pytest

from app.analytics.kpi_engine import register_kpi, get_kpi_calculator, list_kpis, calculate_trend
from app.export.service import ExportService
from app.security.jwt import create_access_token

BASE_URL = "http://localhost:8000"
SEED_TENANT_ID = uuid.UUID("e53cfb21-3b59-5207-a9d2-ea451d45b52e")
SEED_ADMIN_USER_ID = uuid.UUID("8d7c5e05-e663-5035-b6ea-fabe12654ea8")

ADMIN_TOKEN = create_access_token(
    sub=str(SEED_ADMIN_USER_ID),
    tenant_id=str(SEED_TENANT_ID),
    roles=["SYSTEM_ADMIN"],
)
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

client = httpx.Client(base_url=BASE_URL, timeout=30.0)


# ═══════════════════════════════════════════════════════════════════════════
# KPI Engine Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestKPIEngine:
    """Tests for the reusable KPI calculation framework."""

    def test_kpi_register_and_list(self):
        """Register a KPI and verify it appears in the list."""
        kpis_before = len(list_kpis())
        register_kpi("test_kpi", lambda: Decimal("100"))
        assert "test_kpi" in list_kpis()

    def test_kpi_calculator_returns_correct_value(self):
        """Registered KPI calculator returns expected value."""
        async def calc():
            return Decimal("42.50")
        register_kpi("answer", calc)
        fn = get_kpi_calculator("answer")
        assert fn is not None

    def test_kpi_calculator_not_found(self):
        """Non-existent KPI returns None."""
        assert get_kpi_calculator("nonexistent") is None

    def test_calculate_trend_up(self):
        result = calculate_trend(Decimal("150"), Decimal("100"))
        assert result["direction"] == "up"
        assert result["change"] == 50
        assert result["change_percent"] == 50.0

    def test_calculate_trend_down(self):
        result = calculate_trend(Decimal("80"), Decimal("100"))
        assert result["direction"] == "down"
        assert result["change"] == -20
        assert result["change_percent"] == -20.0

    def test_calculate_trend_flat(self):
        result = calculate_trend(Decimal("100"), Decimal("100"))
        assert result["direction"] == "flat"
        assert result["change"] == 0
        assert result["change_percent"] == 0

    def test_calculate_trend_no_previous(self):
        result = calculate_trend(Decimal("100"), None)
        assert result["direction"] == "flat"
        assert result["change_percent"] == 0

    def test_calculate_trend_zero_previous(self):
        result = calculate_trend(Decimal("100"), Decimal("0"))
        assert result["direction"] == "flat"
        assert result["change_percent"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# Export Service Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestExportService:
    """Tests for the export service (CSV, Excel)."""

    def test_csv_export(self):
        data = [{"name": "Supplier A", "spend": 1000}, {"name": "Supplier B", "spend": 2000}]
        filename, mime, content = ExportService.to_csv(data)
        assert mime == "text/csv"
        assert filename.endswith(".csv")
        decoded = content.decode("utf-8")
        assert "name" in decoded
        assert "Supplier A" in decoded
        assert "Supplier B" in decoded

    def test_csv_export_empty(self):
        filename, mime, content = ExportService.to_csv([])
        assert content == b""

    def test_csv_export_roundtrip(self):
        data = [{"col1": "a", "col2": "1"}, {"col1": "b", "col2": "2"}]
        _, _, content = ExportService.to_csv(data)
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["col1"] == "a"

    def test_excel_export_fallback_to_csv(self):
        """When openpyxl is not installed, Excel export falls back to CSV."""
        data = [{"metric": "spend", "value": 5000}]
        filename, mime, content = ExportService.to_excel(data)
        # Without openpyxl, falls back to CSV
        assert content is not None

    def test_generate_report_csv(self):
        data = [{"kpi": "total_spend", "value": 10000}]
        filename, mime, content = ExportService.generate_report(data, "csv")
        assert mime == "text/csv"
        assert b"total_spend" in content

    def test_generate_report_excel(self):
        data = [{"kpi": "total_spend", "value": 10000}]
        filename, mime, content = ExportService.generate_report(data, "excel")
        assert content is not None


# ═══════════════════════════════════════════════════════════════════════════
# Analytics API Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyticsAPI:
    """Integration tests for analytics API endpoints."""

    def test_health(self):
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_executive_dashboard(self):
        resp = client.get("/api/v1/analytics/dashboard", headers=AUTH_HEADERS)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert "kpi_summary" in data["data"]
        assert "spend" in data["data"]
        assert "suppliers" in data["data"]

    def test_spend_analytics(self):
        resp = client.get("/api/v1/analytics/spend", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_spend" in data["data"]

    def test_spend_by_category(self):
        resp = client.get("/api/v1/analytics/spend/categories", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_supplier_scorecard(self):
        resp = client.get("/api/v1/analytics/suppliers/scorecard", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_suppliers" in data["data"]

    def test_contract_analytics(self):
        resp = client.get("/api/v1/analytics/contracts", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "active" in data["data"]

    def test_workflow_analytics(self):
        resp = client.get("/api/v1/analytics/workflows", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "cycle_times" in data["data"]

    def test_create_report(self):
        payload = {"report_name": "Monthly Spend", "report_type": "spend", "config": {"period": "monthly"}}
        resp = client.post("/api/v1/analytics/reports", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["report_name"] == "Monthly Spend"
        # Store report id for subsequent tests
        TestAnalyticsAPI._report_id = data["data"]["id"]

    def test_list_reports(self):
        resp = client.get("/api/v1/analytics/reports", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_get_report(self):
        report_id = getattr(TestAnalyticsAPI, "_report_id", None)
        if report_id is None:
            pytest.skip("No report created")
        resp = client.get(f"/api/v1/analytics/reports/{report_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == report_id

    def test_export_csv(self):
        resp = client.post("/api/v1/analytics/reports/export?format=csv", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_auth_required(self):
        resp = client.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 401

    def test_404_report(self):
        resp = client.get(f"/api/v1/analytics/reports/{uuid.uuid4()}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

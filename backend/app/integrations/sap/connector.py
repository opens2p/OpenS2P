"""
SAP mock connector \u2014 simulates SAP ERP integration.
In production, this would use SAP RFC / OData / SOAP APIs.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from app.integrations.base.connector import BaseConnector, ConnectionConfig, SyncResult
from app.integrations.base.exceptions import AuthenticationError, ExtractionError


class SAPMockConnector(BaseConnector):
    """Mock SAP connector for development/testing."""

    MOCK_VENDORS = [
        {"id": "SAP-VENDOR-001", "name": "SAP Mock Corp", "email": "vendor@sapmock.com", "status": "ACTIVE"},
        {"id": "SAP-VENDOR-002", "name": "Global Parts GmbH", "email": "info@globalparts.de", "status": "ACTIVE"},
        {"id": "SAP-VENDOR-003", "name": "TechSupply Ltd", "email": "sales@techsupply.co.uk", "status": "BLOCKED"},
    ]

    MOCK_PURCHASE_ORDERS = [
        {"id": "SAP-PO-2026-001", "vendor_id": "SAP-VENDOR-001", "total": 125000.00, "currency": "USD", "status": "APPROVED"},
        {"id": "SAP-PO-2026-002", "vendor_id": "SAP-VENDOR-002", "total": 45000.00, "currency": "EUR", "status": "PENDING"},
        {"id": "SAP-PO-2026-003", "vendor_id": "SAP-VENDOR-001", "total": 8900.00, "currency": "USD", "status": "CLOSED"},
    ]

    MOCK_INVOICES = [
        {"id": "SAP-INV-2026-001", "po_id": "SAP-PO-2026-001", "amount": 125000.00, "currency": "USD", "status": "PAID"},
        {"id": "SAP-INV-2026-002", "po_id": "SAP-PO-2026-002", "amount": 45000.00, "currency": "EUR", "status": "OPEN"},
    ]

    async def authenticate(self) -> bool:
        self._authenticated = True
        return True

    async def test_connection(self) -> bool:
        return await self.authenticate()

    async def extract(self, object_type: str, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self._authenticated:
            await self.authenticate()
        if object_type == "supplier":
            return list(self.MOCK_VENDORS)
        elif object_type == "purchase_order":
            return list(self.MOCK_PURCHASE_ORDERS)
        elif object_type == "invoice":
            return list(self.MOCK_INVOICES)
        raise ExtractionError(f"Unsupported object_type: {object_type}")

    async def transform(self, data: list[dict[str, Any]], object_type: str) -> list[dict[str, Any]]:
        if object_type == "supplier":
            return [self._transform_vendor(item) for item in data]
        elif object_type == "purchase_order":
            return [self._transform_po(item) for item in data]
        elif object_type == "invoice":
            return [self._transform_invoice(item) for item in data]
        return data

    def _transform_vendor(self, vendor: dict) -> dict:
        return {
            "supplier_name": vendor["name"],
            "supplier_number": vendor["id"],
            "extras": {"email": vendor.get("email"), "source": "SAP"},
            "status": "APPROVED" if vendor.get("status") == "ACTIVE" else "BLOCKED",
        }

    def _transform_po(self, po: dict) -> dict:
        return {
            "po_number": po["id"],
            "extras": {"currency": po.get("currency"), "source": "SAP"},
            "total_amount": po.get("total", 0),
        }

    def _transform_invoice(self, inv: dict) -> dict:
        return {
            "invoice_number": inv["id"],
            "amount": inv.get("amount", 0),
            "extras": {"currency": inv.get("currency"), "source": "SAP"},
        }

    async def load(self, data: list[dict[str, Any]], object_type: str) -> SyncResult:
        result = SyncResult()
        result.records_processed = len(data)
        result.records_created = len(data)
        return result

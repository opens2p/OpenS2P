"""
OpenS2P – Invoice API Integration Tests
"""
from __future__ import annotations
import uuid
import httpx
import pytest
from app.security.jwt import create_access_token

BASE_URL = "http://localhost:8000"
SEED_TENANT_ID = uuid.UUID("e53cfb21-3b59-5207-a9d2-ea451d45b52e")
SEED_ADMIN_USER_ID = uuid.UUID("8d7c5e05-e663-5035-b6ea-fabe12654ea8")
ADMIN_TOKEN = create_access_token(sub=str(SEED_ADMIN_USER_ID), tenant_id=str(SEED_TENANT_ID), roles=["SYSTEM_ADMIN"])
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
client = httpx.Client(base_url=BASE_URL, timeout=30.0)


class TestInvoiceCRUD:
    created_invoice_id: uuid.UUID | None = None

    def _create_supplier_and_po(self):
        """Helper: create a supplier + PO and return PO ID."""
        sup_resp = client.post("/api/v1/suppliers", json={"supplier_name": "Inv Test Supplier", "supplier_number": f"SUP-INV-{uuid.uuid4().hex[:8].upper()}"}, headers=AUTH_HEADERS)
        assert sup_resp.status_code == 201
        supplier_id = sup_resp.json()["data"]["id"]
        po_resp = client.post("/api/v1/purchase-orders", json={"supplier_id": supplier_id, "items": [{"description": "Test", "quantity": 1, "price": 500}]}, headers=AUTH_HEADERS)
        assert po_resp.status_code == 201
        return uuid.UUID(po_resp.json()["data"]["id"])

    def test_health(self):
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_01_create_invoice(self):
        po_id = self._create_supplier_and_po()
        payload = {"po_id": str(po_id), "amount": 500.00, "invoice_number": f"INV-{uuid.uuid4().hex[:8].upper()}"}
        resp = client.post("/api/v1/invoices", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert "id" in data["data"]
        TestInvoiceCRUD.created_invoice_id = uuid.UUID(data["data"]["id"])

    def test_02_list_invoices(self):
        resp = client.get("/api/v1/invoices", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_03_get_invoice(self):
        sid = TestInvoiceCRUD.created_invoice_id
        if sid is None: pytest.skip("No invoice created")
        resp = client.get(f"/api/v1/invoices/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(sid)

    def test_04_update_invoice(self):
        sid = TestInvoiceCRUD.created_invoice_id
        if sid is None: pytest.skip("No invoice created")
        resp = client.patch(f"/api/v1/invoices/{sid}", json={"invoice_number": "INV-UPDATED"}, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["invoice_number"] == "INV-UPDATED"

    def test_05_match_invoice(self):
        sid = TestInvoiceCRUD.created_invoice_id
        if sid is None: pytest.skip("No invoice created")
        resp = client.post(f"/api/v1/invoices/{sid}/match", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["match_status"] == "MATCHED"

    def test_06_delete_invoice(self):
        sid = TestInvoiceCRUD.created_invoice_id
        if sid is None: pytest.skip("No invoice created")
        resp = client.delete(f"/api/v1/invoices/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 204

    def test_07_get_deleted_returns_404(self):
        sid = TestInvoiceCRUD.created_invoice_id
        if sid is None: pytest.skip("No invoice created")
        resp = client.get(f"/api/v1/invoices/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_08_get_nonexistent_404(self):
        resp = client.get(f"/api/v1/invoices/{uuid.uuid4()}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

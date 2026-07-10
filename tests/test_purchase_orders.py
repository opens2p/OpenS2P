"""
OpenS2P – Purchase Order API Integration Tests
=================================================
End-to-end test of the purchase order vertical slice against a running server.

Prerequisites:
  1. PostgreSQL is running on localhost:5432
  2. Migrations have been applied (``alembic upgrade head``)
  3. Server is running (``uvicorn app.main:app --port 8000``)
  4. Seed data has been loaded (``python -m app.db.seed``)

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k purchase-order --no-header
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from app.security.jwt import create_access_token

BASE_URL = "http://localhost:8000"

# Seeded tenant + admin user IDs (see app/db/seed.py)
SEED_TENANT_ID = uuid.UUID("e53cfb21-3b59-5207-a9d2-ea451d45b52e")
SEED_ADMIN_USER_ID = uuid.UUID("8d7c5e05-e663-5035-b6ea-fabe12654ea8")

ADMIN_TOKEN = create_access_token(
    sub=str(SEED_ADMIN_USER_ID),
    tenant_id=str(SEED_TENANT_ID),
    roles=["SYSTEM_ADMIN"],
)
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

client = httpx.Client(base_url=BASE_URL, timeout=30.0)


class TestPOCRUD:
    """Tests the full purchase order lifecycle end-to-end."""

    created_po_id: uuid.UUID | None = None

    def test_health(self):
        """Server is running and healthy."""
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_01_create_po(self):
        """POST /api/v1/purchase-orders → 201 with PO data."""
        # First create a supplier to reference
        supplier_number = f"SUP-PO-{uuid.uuid4().hex[:8].upper()}"
        sup_payload = {
            "supplier_name": "PO Test Supplier",
            "supplier_number": supplier_number,
        }
        sup_resp = client.post(
            "/api/v1/suppliers",
            json=sup_payload,
            headers=AUTH_HEADERS,
        )
        assert sup_resp.status_code == 201, f"Expected 201, got {sup_resp.status_code}: {sup_resp.text}"
        supplier_id = sup_resp.json()["data"]["id"]

        payload = {
            "supplier_id": supplier_id,
            "items": [
                {"description": "Widget", "quantity": 100, "price": 9.99},
            ],
        }
        resp = client.post(
            "/api/v1/purchase-orders",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["status"] == "CREATED"
        TestPOCRUD.created_po_id = uuid.UUID(data["data"]["id"])

    def test_02_list_pos(self):
        """GET /api/v1/purchase-orders → 200 with list."""
        resp = client.get("/api/v1/purchase-orders", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_03_get_po(self):
        """GET /api/v1/purchase-orders/{id} → 200 with PO."""
        sid = TestPOCRUD.created_po_id
        if sid is None:
            pytest.skip("No PO created")  # noqa: F821
        resp = client.get(f"/api/v1/purchase-orders/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(sid)

    def test_04_update_po(self):
        """PATCH /api/v1/purchase-orders/{id} → 200."""
        sid = TestPOCRUD.created_po_id
        if sid is None:
            pytest.skip("No PO created")  # noqa: F821
        unique_po = f"PO-UPDATED-{uuid.uuid4().hex[:8].upper()}"
        resp = client.patch(
            f"/api/v1/purchase-orders/{sid}",
            json={"po_number": unique_po},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["po_number"] == unique_po

    def test_05_send_po(self):
        """POST /api/v1/purchase-orders/{id}/send → 200, status=SENT."""
        sid = TestPOCRUD.created_po_id
        if sid is None:
            pytest.skip("No PO created")  # noqa: F821
        resp = client.post(
            f"/api/v1/purchase-orders/{sid}/send",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "SENT"

    def test_06_close_po(self):
        """POST /api/v1/purchase-orders/{id}/close → 200, status=CLOSED."""
        sid = TestPOCRUD.created_po_id
        if sid is None:
            pytest.skip("No PO created")  # noqa: F821
        resp = client.post(
            f"/api/v1/purchase-orders/{sid}/close",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CLOSED"

    def test_07_delete_po(self):
        """DELETE /api/v1/purchase-orders/{id} → 204 (soft-delete)."""
        sid = TestPOCRUD.created_po_id
        if sid is None:
            pytest.skip("No PO created")  # noqa: F821
        resp = client.delete(
            f"/api/v1/purchase-orders/{sid}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}"

    def test_08_get_deleted_returns_404(self):
        """After soft-delete, GET returns 404."""
        sid = TestPOCRUD.created_po_id
        if sid is None:
            pytest.skip("No PO created")  # noqa: F821
        resp = client.get(f"/api/v1/purchase-orders/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_09_get_nonexistent_404(self):
        """GET /api/v1/purchase-orders/{fake_id} → 404."""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/purchase-orders/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

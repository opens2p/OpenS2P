"""
OpenS2P – Purchase Requisition API Integration Tests
======================================================
End-to-end test of the purchase requisition vertical slice against a running server.

Prerequisites:
  1. PostgreSQL is running on localhost:5432
  2. Migrations have been applied (``alembic upgrade head``)
  3. Server is running (``uvicorn app.main:app --port 8000``)
  4. Seed data has been loaded (``python -m app.db.seed``)

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k requisition --no-header
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


class TestPRCRUD:
    """Tests the full purchase requisition lifecycle end-to-end."""

    created_pr_id: uuid.UUID | None = None
    created_supplier_id: uuid.UUID | None = None

    def test_health(self):
        """Server is running and healthy."""
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_01_create_supplier(self):
        """Create a supplier to use in PR tests."""
        payload = {
            "supplier_name": f"PR Test Supplier {uuid.uuid4().hex[:8]}",
            "supplier_number": f"SUP-TEST-{uuid.uuid4().hex[:8].upper()}",
        }
        resp = client.post("/api/v1/suppliers", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 201, f"Supplier creation failed: {resp.text}"
        TestPRCRUD.created_supplier_id = uuid.UUID(resp.json()["data"]["id"])

    def test_02_create_pr(self):
        """POST /api/v1/purchase-requisitions → 201 with PR data."""
        sid = TestPRCRUD.created_supplier_id
        if sid is None:
            pytest.skip("No supplier created")
        payload = {
            "supplier_id": str(sid),
            "description": "Test PR",
            "items": [
                {"description": "Item 1", "quantity": 10, "unit_price": 50},
            ],
        }
        resp = client.post(
            "/api/v1/purchase-requisitions",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert "id" in data["data"]
        TestPRCRUD.created_pr_id = uuid.UUID(data["data"]["id"])

    def test_03_list_prs(self):
        """GET /api/v1/purchase-requisitions → 200 with list."""
        resp = client.get("/api/v1/purchase-requisitions", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_04_get_pr(self):
        """GET /api/v1/purchase-requisitions/{id} → 200 with PR."""
        sid = TestPRCRUD.created_pr_id
        if sid is None:
            pytest.skip("No PR created")
        resp = client.get(f"/api/v1/purchase-requisitions/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(sid)

    def test_05_update_pr(self):
        """PATCH /api/v1/purchase-requisitions/{id} → 200."""
        sid = TestPRCRUD.created_pr_id
        if sid is None:
            pytest.skip("No PR created")
        resp = client.patch(
            f"/api/v1/purchase-requisitions/{sid}",
            json={"description": "Updated"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["description"] == "Updated"

    def test_06_approve_pr(self):
        """POST /api/v1/purchase-requisitions/{id}/approve → 200, status=APPROVED."""
        sid = TestPRCRUD.created_pr_id
        if sid is None:
            pytest.skip("No PR created")
        resp = client.post(
            f"/api/v1/purchase-requisitions/{sid}/approve",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        # Approving a PR with a supplier auto-creates a PO → status becomes ORDERED
        assert resp.json()["data"]["status"] in ("APPROVED", "ORDERED")

    def test_07_reject_new_pr(self):
        """Create a fresh PR, then reject it."""
        payload = {"description": "Reject me"}
        create_resp = client.post(
            "/api/v1/purchase-requisitions",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert create_resp.status_code == 201
        reject_id = uuid.UUID(create_resp.json()["data"]["id"])

        resp = client.post(
            f"/api/v1/purchase-requisitions/{reject_id}/reject",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "REJECTED"

    def test_08_delete_pr(self):
        """DELETE /api/v1/purchase-requisitions/{id} → 204 (soft-delete)."""
        sid = TestPRCRUD.created_pr_id
        if sid is None:
            pytest.skip("No PR created")
        resp = client.delete(
            f"/api/v1/purchase-requisitions/{sid}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}"

    def test_08_get_deleted_returns_404(self):
        """After soft-delete, GET returns 404."""
        sid = TestPRCRUD.created_pr_id
        if sid is None:
            pytest.skip("No PR created")
        resp = client.get(f"/api/v1/purchase-requisitions/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_09_get_nonexistent_404(self):
        """GET /api/v1/purchase-requisitions/{fake_id} → 404."""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/purchase-requisitions/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

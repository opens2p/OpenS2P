"""
OpenS2P – Supplier API Integration Tests
===========================================
End-to-end test of the supplier vertical slice against a running server.

Prerequisites:
  1. PostgreSQL is running on localhost:5432
  2. Migrations have been applied (``alembic upgrade head``)
  3. Server is running (``uvicorn app.main:app --port 8000``)
  4. Seed data has been loaded (``python -m app.db.seed``)

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k supplier --no-header
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


class TestSupplierCRUD:
    """Tests the full supplier lifecycle end-to-end."""

    created_supplier_id: uuid.UUID | None = None

    def _unique_supplier_number(self, prefix: str = "SUP") -> str:
        """Generate a unique supplier number for each test run."""
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def test_health(self):
        """Server is running and healthy."""
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_01_create_supplier(self):
        """POST /api/v1/suppliers → 201 with supplier data."""
        supplier_number = self._unique_supplier_number("SUP-ACM")
        payload = {
            "supplier_name": "Acme Corporation",
            "supplier_number": supplier_number,
            "description": "Created during integration test",
            "address": "742 Evergreen Terrace, Springfield",
        }
        resp = client.post(
            "/api/v1/suppliers",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["supplier_name"] == "Acme Corporation"
        assert data["data"]["supplier_number"] == supplier_number
        assert data["data"]["status"] == "DRAFT"
        assert "id" in data["data"]
        TestSupplierCRUD.created_supplier_id = uuid.UUID(data["data"]["id"])

    def test_02_list_suppliers(self):
        """GET /api/v1/suppliers → 200 with list."""
        resp = client.get("/api/v1/suppliers", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_03_get_supplier(self):
        """GET /api/v1/suppliers/{id} → 200 with supplier."""
        sid = TestSupplierCRUD.created_supplier_id
        if sid is None:
            pytest.skip("No supplier created")  # noqa: F821
        resp = client.get(f"/api/v1/suppliers/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(sid)

    def test_04_update_supplier(self):
        """PATCH /api/v1/suppliers/{id} → 200."""
        sid = TestSupplierCRUD.created_supplier_id
        if sid is None:
            pytest.skip("No supplier created")  # noqa: F821
        resp = client.patch(
            f"/api/v1/suppliers/{sid}",
            json={"description": "Updated description"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["description"] == "Updated description"

    def test_05_approve_supplier(self):
        """POST /api/v1/suppliers/{id}/approve → 200, status=APPROVED."""
        sid = TestSupplierCRUD.created_supplier_id
        if sid is None:
            pytest.skip("No supplier created")  # noqa: F821
        resp = client.post(
            f"/api/v1/suppliers/{sid}/approve",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "APPROVED"

    def test_06_delete_supplier(self):
        """DELETE /api/v1/suppliers/{id} → 204 (soft-delete)."""
        sid = TestSupplierCRUD.created_supplier_id
        if sid is None:
            pytest.skip("No supplier created")  # noqa: F821
        resp = client.delete(
            f"/api/v1/suppliers/{sid}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}"

    def test_07_get_deleted_returns_404(self):
        """After soft-delete, GET returns 404."""
        sid = TestSupplierCRUD.created_supplier_id
        if sid is None:
            pytest.skip("No supplier created")  # noqa: F821
        resp = client.get(f"/api/v1/suppliers/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_08_get_nonexistent_404(self):
        """GET /api/v1/suppliers/{fake_id} → 404."""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/suppliers/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_09_block_supplier(self):
        """POST /api/v1/suppliers/{id}/block → 200, status=BLOCKED."""
        payload = {
            "supplier_name": "Blocked Corp",
            "supplier_number": self._unique_supplier_number("SUP-BLK"),
        }
        create_resp = client.post(
            "/api/v1/suppliers",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert create_resp.status_code == 201
        block_id = uuid.UUID(create_resp.json()["data"]["id"])

        resp = client.post(
            f"/api/v1/suppliers/{block_id}/block",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "BLOCKED"

"""
OpenS2P – Contract API Integration Tests
===========================================
End-to-end test of the contract vertical slice against a running server.

Prerequisites:
  1. PostgreSQL is running on localhost:5432
  2. Migrations have been applied (``alembic upgrade head``)
  3. Server is running (``uvicorn app.main:app --port 8000``)
  4. Seed data has been loaded (``python -m app.db.seed``)

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k contract --no-header
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


class TestContractCRUD:
    """Full contract lifecycle tests."""

    created_contract_id: uuid.UUID | None = None

    def test_health(self):
        """Server is running and healthy."""
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_01_create_contract(self):
        """POST /api/v1/contracts → 201 with contract data."""
        # First create a supplier to reference
        sup_resp = client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "Contract Test Supplier",
                "supplier_number": f"SUP-CT-{uuid.uuid4().hex[:8].upper()}",
            },
            headers=AUTH_HEADERS,
        )
        assert sup_resp.status_code == 201
        supplier_id = sup_resp.json()["data"]["id"]

        payload = {
            "supplier_id": supplier_id,
            "contract_number": f"CTR-{uuid.uuid4().hex[:8].upper()}",
            "contract_value": 100000.00,
            "description": "Test contract",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }
        resp = client.post("/api/v1/contracts", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        # Decimal fields are serialised as strings by FastAPI / Pydantic v2
        assert data["data"]["contract_value"] == "100000.0"
        assert "id" in data["data"]
        TestContractCRUD.created_contract_id = uuid.UUID(data["data"]["id"])

    def test_02_list_contracts(self):
        """GET /api/v1/contracts → 200 with list."""
        resp = client.get("/api/v1/contracts", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_03_get_contract(self):
        """GET /api/v1/contracts/{id} → 200 with contract."""
        sid = TestContractCRUD.created_contract_id
        if sid is None:
            pytest.skip("No contract created")
        resp = client.get(f"/api/v1/contracts/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(sid)

    def test_04_update_contract(self):
        """PATCH /api/v1/contracts/{id} → 200."""
        sid = TestContractCRUD.created_contract_id
        if sid is None:
            pytest.skip("No contract created")
        resp = client.patch(
            f"/api/v1/contracts/{sid}",
            json={"description": "Updated"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["description"] == "Updated"

    def test_05_activate_contract(self):
        """POST /api/v1/contracts/{id}/activate → 200."""
        sid = TestContractCRUD.created_contract_id
        if sid is None:
            pytest.skip("No contract created")
        resp = client.post(
            f"/api/v1/contracts/{sid}/activate",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200

    def test_06_delete_contract(self):
        """DELETE /api/v1/contracts/{id} → 204 (soft-delete)."""
        sid = TestContractCRUD.created_contract_id
        if sid is None:
            pytest.skip("No contract created")
        resp = client.delete(
            f"/api/v1/contracts/{sid}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"

    def test_07_get_deleted_returns_404(self):
        """After soft-delete, GET returns 404."""
        sid = TestContractCRUD.created_contract_id
        if sid is None:
            pytest.skip("No contract created")
        resp = client.get(f"/api/v1/contracts/{sid}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_08_get_nonexistent_404(self):
        """GET /api/v1/contracts/{fake_id} → 404."""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/contracts/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

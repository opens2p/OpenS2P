"""
OpenS2P – Integration API & Connector Tests
==============================================
End-to-end tests for the integration framework (Phase 6).

Prerequisites:
  1. PostgreSQL is running on localhost:5432
  2. Migrations have been applied (``alembic upgrade head``)
  3. Server is running (``uvicorn app.main:app --port 8000``)
  4. Seed data has been loaded (``python -m app.db.seed``)

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k integration --no-header
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from app.security.jwt import create_access_token

BASE_URL = "http://localhost:8000"

# Seeded tenant + admin user IDs
SEED_TENANT_ID = uuid.UUID("e53cfb21-3b59-5207-a9d2-ea451d45b52e")
SEED_ADMIN_USER_ID = uuid.UUID("8d7c5e05-e663-5035-b6ea-fabe12654ea8")

ADMIN_TOKEN = create_access_token(
    sub=str(SEED_ADMIN_USER_ID),
    tenant_id=str(SEED_TENANT_ID),
    roles=["SYSTEM_ADMIN"],
)
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

client = httpx.Client(base_url=BASE_URL, timeout=30.0)

# ── Helpers ────────────────────────────────────────────────────────────────


def random_connection_name() -> str:
    return f"Test-Conn-{uuid.uuid4().hex[:8]}"


def create_sap_connection_payload() -> dict:
    return {
        "connection_name": random_connection_name(),
        "connector_type": "sap",
        "endpoint_url": "https://sap.example.com/rfc",
        "auth_type": "basic",
        "credentials": {"username": "testuser", "password": "secret123"},
        "config": {"system_id": "PRD", "client": "100"},
    }


# ── Tests ──────────────────────────────────────────────────────────────────


class TestIntegrationConnectorUnit:
    """Unit tests for connector classes (no server needed)."""

    def test_sap_connector_authenticate(self):
        """SAP mock connector authenticates successfully."""
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        import asyncio
        result = asyncio.run(connector.authenticate())
        assert result is True
        assert connector._authenticated is True

    def test_sap_connector_extract_suppliers(self):
        """SAP mock connector extracts suppliers."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        data = asyncio.run(connector.extract("supplier"))
        assert len(data) == 3
        assert data[0]["name"] == "SAP Mock Corp"

    def test_sap_connector_extract_unsupported_raises(self):
        """Extracting unsupported object_type raises ExtractionError."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        from app.integrations.base.exceptions import ExtractionError
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        with pytest.raises(ExtractionError):
            asyncio.run(connector.extract("contract"))

    def test_sap_connector_transform_suppliers(self):
        """SAP vendor data transforms to OpenS2P supplier format."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        raw = [{"id": "V001", "name": "Test Corp", "email": "t@t.com", "status": "ACTIVE"}]
        transformed = asyncio.run(connector.transform(raw, "supplier"))
        assert len(transformed) == 1
        assert transformed[0]["supplier_name"] == "Test Corp"
        assert transformed[0]["supplier_number"] == "V001"
        assert transformed[0]["status"] == "APPROVED"

    def test_sap_connector_transform_blocked_supplier(self):
        """SAP BLOCKED vendor becomes BLOCKED in OpenS2P."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        raw = [{"id": "V002", "name": "Blocked Ltd", "email": "b@b.com", "status": "BLOCKED"}]
        transformed = asyncio.run(connector.transform(raw, "supplier"))
        assert transformed[0]["status"] == "BLOCKED"

    def test_sap_connector_transform_po(self):
        """SAP PO data transforms correctly."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        raw = [{"id": "PO-001", "total": 5000.00, "currency": "USD", "status": "APPROVED"}]
        transformed = asyncio.run(connector.transform(raw, "purchase_order"))
        assert transformed[0]["po_number"] == "PO-001"
        assert transformed[0]["total_amount"] == 5000.0

    def test_sap_connector_transform_invoice(self):
        """SAP invoice data transforms correctly."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        raw = [{"id": "INV-001", "amount": 999.99, "currency": "USD", "status": "OPEN"}]
        transformed = asyncio.run(connector.transform(raw, "invoice"))
        assert transformed[0]["invoice_number"] == "INV-001"
        assert transformed[0]["amount"] == 999.99

    def test_sap_connector_full_sync(self):
        """Full sync pipeline extract → transform → load."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.sap.connector import SAPMockConnector
        config = ConnectionConfig(connector_type="sap")
        connector = SAPMockConnector(config)
        result = asyncio.run(connector.sync("supplier"))
        assert result.success is True
        assert result.records_processed == 3
        assert result.records_created == 3

    def test_coupa_connector_extract(self):
        """Coupa mock connector extracts suppliers."""
        import asyncio
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.coupa.connector import CoupaMockConnector
        config = ConnectionConfig(connector_type="coupa")
        connector = CoupaMockConnector(config)
        data = asyncio.run(connector.extract("supplier"))
        assert len(data) == 2
        assert data[0]["name"] == "Coupa Supply Co"

    def test_generic_rest_connector_auth_basic(self):
        """Generic REST connector authenticates with basic auth."""
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.generic_rest.connector import GenericRESTConnector
        config = ConnectionConfig(
            auth_type="basic",
            credentials={"username": "admin", "password": "pass"},
        )
        connector = GenericRESTConnector(config)
        import asyncio
        result = asyncio.run(connector.authenticate())
        assert result is True

    def test_generic_rest_connector_auth_api_key(self):
        """Generic REST connector authenticates with API key."""
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.generic_rest.connector import GenericRESTConnector
        config = ConnectionConfig(
            auth_type="api_key",
            credentials={"api_key": "abc123"},
        )
        connector = GenericRESTConnector(config)
        import asyncio
        result = asyncio.run(connector.authenticate())
        assert result is True

    def test_generic_rest_connector_auth_missing_returns_false(self):
        """Missing credentials returns False for basic auth."""
        from app.integrations.base.connector import ConnectionConfig
        from app.integrations.generic_rest.connector import GenericRESTConnector
        config = ConnectionConfig(
            auth_type="basic",
            credentials={"username": "admin"},
        )
        connector = GenericRESTConnector(config)
        import asyncio
        result = asyncio.run(connector.authenticate())
        assert result is False

    def test_credential_masking(self):
        """Sensitive credential fields are masked."""
        from app.integrations.base.credentials import mask_credentials
        creds = {"username": "admin", "password": "supersecret", "api_key": "key12345"}
        masked = mask_credentials(creds)
        assert masked["username"] == "admin"
        assert masked["password"] == "supe****"
        assert masked["api_key"] == "key1****"

    def test_credential_masking_none(self):
        """None credentials returns None."""
        from app.integrations.base.credentials import mask_credentials
        assert mask_credentials(None) is None

    def test_credential_validation_basic(self):
        """Basic auth requires username and password."""
        from app.integrations.base.credentials import validate_credentials
        missing = validate_credentials({"username": "admin"}, "basic")
        assert "password" in missing
        assert len(missing) == 1

    def test_credential_validation_api_key(self):
        """API key auth requires api_key field."""
        from app.integrations.base.credentials import validate_credentials
        missing = validate_credentials({}, "api_key")
        assert "api_key" in missing

    def test_credential_validation_oauth2(self):
        """OAuth2 auth requires client_id, client_secret, token_url."""
        from app.integrations.base.credentials import validate_credentials
        missing = validate_credentials({"client_id": "myid"}, "oauth2")
        assert "client_secret" in missing
        assert "token_url" in missing

    def test_health(self):
        """Server is running and healthy."""
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


class TestIntegrationAPI:
    """End-to-end tests for the integration REST API."""

    created_connection_id: uuid.UUID | None = None

    def test_01_create_connection(self):
        """POST /api/v1/integrations/connections → 201."""
        payload = create_sap_connection_payload()
        resp = client.post(
            "/api/v1/integrations/connections",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["connection_name"] == payload["connection_name"]
        assert data["data"]["connector_type"] == "sap"
        assert "id" in data["data"]
        TestIntegrationAPI.created_connection_id = uuid.UUID(data["data"]["id"])

    def test_02_list_connections(self):
        """GET /api/v1/integrations/connections → 200 with list."""
        resp = client.get("/api/v1/integrations/connections", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_03_get_connection(self):
        """GET /api/v1/integrations/connections/{id} → 200."""
        cid = TestIntegrationAPI.created_connection_id
        if cid is None:
            pytest.skip("No connection created")
        resp = client.get(f"/api/v1/integrations/connections/{cid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(cid)

    def test_04_update_connection(self):
        """PATCH /api/v1/integrations/connections/{id} → 200."""
        cid = TestIntegrationAPI.created_connection_id
        if cid is None:
            pytest.skip("No connection created")
        resp = client.patch(
            f"/api/v1/integrations/connections/{cid}",
            json={"connection_name": "Updated-SAP-Conn"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["connection_name"] == "Updated-SAP-Conn"

    def test_05_test_connection(self):
        """POST /api/v1/integrations/connections/{id}/test → 200."""
        cid = TestIntegrationAPI.created_connection_id
        if cid is None:
            pytest.skip("No connection created")
        resp = client.post(
            f"/api/v1/integrations/connections/{cid}/test",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "connected" in data["data"]

    def test_06_sync_connection(self):
        """POST /api/v1/integrations/connections/{id}/sync → 200."""
        cid = TestIntegrationAPI.created_connection_id
        if cid is None:
            pytest.skip("No connection created")
        resp = client.post(
            f"/api/v1/integrations/connections/{cid}/sync",
            json={"object_type": "supplier"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] in ("completed", "failed")
        assert "run_id" in data["data"]

    def test_07_list_runs(self):
        """GET /api/v1/integrations/runs → 200."""
        resp = client.get("/api/v1/integrations/runs", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # Should have at least one run from the sync test
        if TestIntegrationAPI.created_connection_id:
            cid = TestIntegrationAPI.created_connection_id
            resp2 = client.get(
                f"/api/v1/integrations/runs?connection_id={cid}",
                headers=AUTH_HEADERS,
            )
            assert resp2.status_code == 200

    def test_08_get_nonexistent_connection_404(self):
        """GET /api/v1/integrations/connections/{fake} → 404."""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/integrations/connections/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_09_delete_connection(self):
        """DELETE /api/v1/integrations/connections/{id} → 204."""
        # Create a temp connection to delete
        payload = create_sap_connection_payload()
        create_resp = client.post(
            "/api/v1/integrations/connections",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert create_resp.status_code == 201
        del_id = uuid.UUID(create_resp.json()["data"]["id"])

        resp = client.delete(
            f"/api/v1/integrations/connections/{del_id}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = client.get(
            f"/api/v1/integrations/connections/{del_id}",
            headers=AUTH_HEADERS,
        )
        assert get_resp.status_code == 404

    def test_10_auth_required(self):
        """Endpoints return 401 without auth token."""
        resp = client.get("/api/v1/integrations/connections")
        assert resp.status_code == 401

    def test_11_create_connection_invalid_type(self):
        """Invalid connector_type returns 422."""
        payload = create_sap_connection_payload()
        payload["connector_type"] = "invalid_erp"
        resp = client.post(
            "/api/v1/integrations/connections",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 422

    def test_12_delete_nonexistent_returns_404(self):
        """DELETE on nonexistent connection returns 404."""
        fake_id = uuid.uuid4()
        resp = client.delete(
            f"/api/v1/integrations/connections/{fake_id}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_13_update_nonexistent_returns_404(self):
        """PATCH on nonexistent connection returns 404."""
        fake_id = uuid.uuid4()
        resp = client.patch(
            f"/api/v1/integrations/connections/{fake_id}",
            json={"connection_name": "Nope"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_14_test_nonexistent_returns_404(self):
        """Test on nonexistent connection returns 404."""
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/integrations/connections/{fake_id}/test",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_15_sync_nonexistent_returns_404(self):
        """Sync on nonexistent connection returns 404."""
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/integrations/connections/{fake_id}/sync",
            json={"object_type": "supplier"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

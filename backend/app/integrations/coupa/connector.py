"""
Coupa mock connector \u2014 simulates Coupa procurement platform integration.
"""
from __future__ import annotations
from typing import Any
from app.integrations.base.connector import BaseConnector, ConnectionConfig, SyncResult


class CoupaMockConnector(BaseConnector):
    """Mock Coupa connector for development/testing."""

    MOCK_SUPPLIERS = [
        {"id": "CP-001", "name": "Coupa Supply Co", "status": "active"},
        {"id": "CP-002", "name": "OfficeWorks Pro", "status": "active"},
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
            return list(self.MOCK_SUPPLIERS)
        return []

    async def transform(self, data: list[dict[str, Any]], object_type: str) -> list[dict[str, Any]]:
        if object_type == "supplier":
            return [{"supplier_name": s["name"], "supplier_number": s["id"], "extras": {"source": "Coupa"}} for s in data]
        return data

    async def load(self, data: list[dict[str, Any]], object_type: str) -> SyncResult:
        result = SyncResult()
        result.records_processed = len(data)
        result.records_created = len(data)
        return result

"""
Generic REST API connector \u2014 connects to any REST-based system.
"""
from __future__ import annotations
import base64
import httpx
from typing import Any
from app.integrations.base.connector import BaseConnector, ConnectionConfig, SyncResult
from app.integrations.base.exceptions import AuthenticationError, ConnectionError, ExtractionError


class GenericRESTConnector(BaseConnector):
    """Connects to any REST API with configurable endpoints."""

    async def authenticate(self) -> bool:
        if self.config.auth_type == "basic" and self.config.credentials:
            return bool(self.config.credentials.get("username") and self.config.credentials.get("password"))
        elif self.config.auth_type == "api_key" and self.config.credentials:
            return bool(self.config.credentials.get("api_key"))
        elif self.config.auth_type == "oauth2":
            return bool(self.config.credentials)
        return True

    async def test_connection(self) -> bool:
        if not self.config.endpoint_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.config.endpoint_url)
                return resp.status_code < 500
        except Exception:
            return False

    async def extract(self, object_type: str, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self._authenticated:
            await self.authenticate()
        endpoint = (self.config.config or {}).get(f"endpoint_{object_type}", f"/api/{object_type}")
        url = f"{self.config.endpoint_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = self._build_headers()
                resp = await client.get(url, headers=headers, params=filter_params)
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, list) else data.get("data", data.get("results", []))
        except Exception as e:
            raise ExtractionError(f"REST extract failed: {e}")

    async def transform(self, data: list[dict[str, Any]], object_type: str) -> list[dict[str, Any]]:
        return data

    async def load(self, data: list[dict[str, Any]], object_type: str) -> SyncResult:
        result = SyncResult()
        result.records_processed = len(data)
        result.records_created = len(data)
        return result

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.auth_type == "api_key" and self.config.credentials:
            headers["X-API-Key"] = self.config.credentials.get("api_key", "")
        elif self.config.auth_type == "basic" and self.config.credentials:
            creds = f"{self.config.credentials.get('username', '')}:{self.config.credentials.get('password', '')}"
            headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"
        return headers

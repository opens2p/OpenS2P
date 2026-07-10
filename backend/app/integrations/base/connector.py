"""
Abstract base connector that all ERP adapters implement.
"""
from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ConnectionConfig:
    """Configuration for an external system connection."""
    id: uuid.UUID | None = None
    tenant_id: uuid.UUID | None = None
    connection_name: str = ""
    connector_type: str = ""
    endpoint_url: str | None = None
    auth_type: str | None = None
    credentials: dict[str, Any] | None = None
    config: dict[str, Any] | None = None


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool = True
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    errors: list[dict[str, Any]] | None = None
    run_id: uuid.UUID | None = None


class BaseConnector(ABC):
    """Every ERP adapter inherits from this class."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external system."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify connectivity to the external system."""
        ...

    @abstractmethod
    async def extract(self, object_type: str, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Pull data from the external system."""
        ...

    @abstractmethod
    async def transform(self, data: list[dict[str, Any]], object_type: str) -> list[dict[str, Any]]:
        """Transform external data format to OpenS2P format."""
        ...

    @abstractmethod
    async def load(self, data: list[dict[str, Any]], object_type: str) -> SyncResult:
        """Push transformed data into OpenS2P models."""
        ...

    async def sync(self, object_type: str) -> SyncResult:
        """Full extract \u2192 transform \u2192 load pipeline."""
        raw_data = await self.extract(object_type)
        transformed = await self.transform(raw_data, object_type)
        result = await self.load(transformed, object_type)
        return result

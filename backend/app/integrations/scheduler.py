"""
Simple sync scheduler for periodic data synchronization.
In production, use Celery Beat or APScheduler.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from app.integrations.base.connector import ConnectionConfig
from app.integrations.sap.client import create_sap_connector


async def run_sync(
    connection_id: uuid.UUID,
    connector_type: str,
    object_type: str,
    config: ConnectionConfig,
) -> dict[str, Any]:
    """Execute a sync operation for a given connection and object type."""
    if connector_type == "sap":
        connector = create_sap_connector(config)
    else:
        raise ValueError(f"Unsupported connector type: {connector_type}")

    result = await connector.sync(object_type)
    return {
        "run_id": str(uuid.uuid4()),
        "connection_id": str(connection_id),
        "object_type": object_type,
        "status": "completed" if result.success else "failed",
        "records_processed": result.records_processed,
        "records_created": result.records_created,
        "records_updated": result.records_updated,
        "records_failed": result.records_failed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

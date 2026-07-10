"""
Pydantic schemas for integration operations.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    connection_name: str = Field(..., min_length=1, max_length=200)
    connector_type: str = Field(..., pattern="^(sap|coupa|oracle|netsuite|generic_rest)$")
    endpoint_url: str | None = None
    auth_type: str | None = Field(None, pattern="^(basic|oauth2|api_key|certificate)$")
    credentials: dict[str, Any] | None = None
    config: dict[str, Any] | None = None


class ConnectionUpdate(BaseModel):
    connection_name: str | None = None
    endpoint_url: str | None = None
    auth_type: str | None = None
    credentials: dict[str, Any] | None = None
    config: dict[str, Any] | None = None


class ConnectionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    connection_name: str
    connector_type: str
    endpoint_url: str | None = None
    auth_type: str | None = None
    is_connected: bool = False
    last_test_at: datetime | None = None
    last_sync_at: datetime | None = None
    tenant_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SyncRequest(BaseModel):
    object_type: str = Field(..., pattern="^(supplier|purchase_order|invoice|contract|payment)$")


class SyncResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    errors: list[dict[str, Any]] | None = None


class RunResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    connection_id: uuid.UUID
    direction: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    records_processed: int | None = None
    errors: dict[str, Any] | None = None
    created_at: datetime | None = None


class LogResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    run_id: uuid.UUID
    level: str
    message: str
    object_type: str | None = None
    object_id: str | None = None
    details: dict[str, Any] | None = None
    created_at: datetime | None = None

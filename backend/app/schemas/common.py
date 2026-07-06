"""
OpenS2P – Common Pydantic schemas
===================================
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


# ── pagination ────────────────────────────────────────────────────────────


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 50


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: list[DataT]
    total: int
    skip: int
    limit: int


# ── standard API response wrappers ────────────────────────────────────────


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT | None = None
    message: str | None = None


class ApiError(BaseModel):
    success: bool = False
    detail: str
    errors: list[dict[str, Any]] | None = None


# ── audit fields (used by many schemas) ────────────────────────────────────


class AuditFields(BaseModel):
    """Read-only audit metadata returned in responses."""

    created_at: datetime | None = None
    created_by: uuid.UUID | None = None
    updated_at: datetime | None = None
    updated_by: uuid.UUID | None = None
    is_active: bool = True

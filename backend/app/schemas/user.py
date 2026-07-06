"""
OpenS2P – User schemas
=======================
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.schemas.common import AuditFields


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    password: str = Field(..., min_length=8)


class UserResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    is_superuser: bool = False
    tenant_id: uuid.UUID


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None


class RoleResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_name: str
    description: str | None = None
    tenant_id: uuid.UUID


class RoleAssignment(BaseModel):
    role_id: uuid.UUID

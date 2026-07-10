"""
OpenS2P – Workflow schemas
===========================
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import WorkflowStatus
from app.schemas.common import AuditFields


class WorkflowStartRequest(BaseModel):
    object_type: str
    object_id: uuid.UUID


class DecisionRequest(BaseModel):
    decision: str  # "approve" | "reject"
    payload: dict[str, Any] | None = None


class EscalationRequest(BaseModel):
    new_approver_id: uuid.UUID
    reason: str | None = None


class ApproveRequest(BaseModel):
    payload: dict[str, Any] | None = None


class RejectRequest(BaseModel):
    reason: str | None = None


class ApprovalTaskResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    approver_id: uuid.UUID | None = None
    status: str | None = None
    payload: dict[str, Any] | None = None
    completed_at: datetime | None = None
    tenant_id: uuid.UUID
    step_name: str | None = None
    assigned_role: str | None = None
    comments: str | None = None


class WorkflowResponse(AuditFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_type: str
    object_id: uuid.UUID
    status: WorkflowStatus
    started_at: datetime | None = None
    tenant_id: uuid.UUID
    workflow_name: str | None = None
    current_step: int | None = None
    wf_metadata: dict[str, Any] | None = None
    tasks: list[ApprovalTaskResponse] | None = None


class WorkflowHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_type: str
    object_id: uuid.UUID
    status: WorkflowStatus
    started_at: datetime | None = None
    created_at: datetime | None = None
    tenant_id: uuid.UUID

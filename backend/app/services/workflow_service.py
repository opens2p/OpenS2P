"""
OpenS2P – Workflow Service (Engine-powered)
=============================================
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models import ApprovalTask, WorkflowInstance
from app.services.uow import UnitOfWork
from app.schemas.serialization import safe_validate
from app.workflow.engine import WorkflowEngine


class WorkflowService:
    """Workflow orchestration powered by the WorkflowEngine."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id
        self.engine = WorkflowEngine(uow, actor_id=actor_id)

    async def start_workflow(
        self,
        object_type: str,
        object_id: uuid.UUID,
    ) -> WorkflowInstance:
        """Initiate a new workflow for a business object (PR, PO, etc.)."""
        return await self.engine.start(object_type, object_id)

    async def approve_task(
        self,
        task_id: uuid.UUID,
        payload: dict[str, Any] | None = None,
    ) -> ApprovalTask | None:
        """Approve an approval task and advance the workflow."""
        return await self.engine.approve(task_id, payload)

    async def reject_task(
        self,
        task_id: uuid.UUID,
        reason: str | None = None,
    ) -> ApprovalTask | None:
        """Reject an approval task and cancel the workflow."""
        return await self.engine.reject(task_id, reason)

    async def get_pending_tasks(self, user_id: uuid.UUID) -> list[ApprovalTask]:
        """Return all outstanding approval tasks for a user."""
        return await self.uow.approval_tasks.list_pending_for(user_id)

    async def get_workflow_history(
        self,
        object_type: str,
        object_id: uuid.UUID,
    ) -> list[WorkflowInstance]:
        """Return workflow history for a business object."""
        return await self.uow.workflows.list_by_object(object_type, object_id)

    async def get_task(self, task_id: uuid.UUID) -> ApprovalTask | None:
        """Get a single approval task by ID."""
        return await self.uow.approval_tasks.get(task_id)

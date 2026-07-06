"""
OpenS2P – Workflow Service
===========================
Orchestrates approval workflows for procurement objects (PR, PO, supplier, invoice).
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models import ApprovalTask, WorkflowInstance
from app.services.uow import UnitOfWork


class WorkflowService:
    """Workflow orchestration — start, decide, escalate."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def start_workflow(
        self,
        object_type: str,
        object_id: uuid.UUID,
    ) -> WorkflowInstance:
        """Initiate a new workflow for a business object (PR, PO, etc.)."""
        wf = await self.uow.workflows.start_workflow(object_type, object_id)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="workflow",
            entity_id=wf.id,
            event_type="WORKFLOW_STARTED",
            new_values={"object_type": object_type, "object_id": str(object_id)},
            created_by=self.actor_id,
        )
        return wf

    async def process_decision(
        self,
        task_id: uuid.UUID,
        decision: str,
        payload: dict[str, Any] | None = None,
    ) -> ApprovalTask | None:
        """Approve or reject an approval task."""
        task = await self.uow.approval_tasks.get(task_id)
        if task is None:
            return None

        if decision == "approve":
            result = await self.uow.approval_tasks.approve(task_id, payload)
            event = "APPROVAL_TASK_APPROVED"
        elif decision == "reject":
            result = await self.uow.approval_tasks.reject(task_id, payload)
            event = "APPROVAL_TASK_REJECTED"
        else:
            return None

        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="approval_task",
            entity_id=task_id,
            event_type=event,
            new_values={"decision": decision, **({"payload": payload} if payload else {})},
            created_by=self.actor_id,
        )
        return result

    async def escalate(
        self,
        task_id: uuid.UUID,
        new_approver_id: uuid.UUID,
        reason: str | None = None,
    ) -> ApprovalTask | None:
        """Reassign an approval task to a different user (escalation)."""
        result = await self.uow.approval_tasks.delegate(task_id, new_approver_id)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="approval_task",
            entity_id=task_id,
            event_type="APPROVAL_TASK_ESCALATED",
            new_values={
                "new_approver_id": str(new_approver_id),
                "reason": reason,
            },
            created_by=self.actor_id,
        )
        return result

    async def get_pending_tasks(self, user_id: uuid.UUID) -> list[ApprovalTask]:
        """Return all outstanding approval tasks for a user."""
        return await self.uow.approval_tasks.list_pending_for(user_id)

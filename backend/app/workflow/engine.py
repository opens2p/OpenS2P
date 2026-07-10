"""
OpenS2P – Workflow Engine
==========================
Orchestrates workflow execution from start to completion.

Flow:
1. find_template(object_type) — finds matching template
2. create_instance() — creates WorkflowInstance
3. create_tasks() — creates ApprovalTask for each step
4. execute_step() — processes current step
5. approve/reject — moves to next step or completes
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models import ApprovalTask, WorkflowInstance


class WorkflowEngine:
    """
    Core workflow engine that drives approval workflows.

    :param uow:       Unit of work providing repository access.
    :param actor_id:  UUID of the user performing actions.
    """

    def __init__(self, uow, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def start(
        self,
        object_type: str,
        object_id: uuid.UUID,
    ) -> WorkflowInstance:
        """Start a new workflow, auto-select template, create tasks."""
        # Find template for object_type
        template = await self._find_template(object_type)

        # Create workflow instance
        wf = await self.uow.workflows.start_workflow(object_type, object_id)

        # Create tasks from template steps
        if template and template.steps:
            tasks = await self._create_tasks(wf.id, template.steps)
        else:
            tasks = []

        # Set to IN_PROGRESS
        wf = await self.uow.workflows.update(
            wf.id,
            {
                "status": "IN_PROGRESS",
                "workflow_name": template.label if template else object_type,
                "wf_metadata": {"steps": [t.payload.get("step") for t in tasks]} if tasks else None,
            },
        )

        # Publish event
        await self._publish_event("WORKFLOW_STARTED", {
            "workflow_id": str(wf.id),
            "object_type": object_type,
            "object_id": str(object_id),
        })

        return wf

    async def approve(
        self,
        task_id: uuid.UUID,
        payload: dict[str, Any] | None = None,
    ) -> ApprovalTask | None:
        """Approve a task and advance the workflow."""
        task = await self.uow.approval_tasks.get(task_id)
        if not task:
            return None

        # Mark task as approved
        task = await self.uow.approval_tasks.approve(task_id, payload)

        # Check if workflow is complete
        wf = await self.uow.workflows.get_with_tasks(task.workflow_id)
        if wf is None:
            return task

        remaining = [t for t in wf.tasks if t.completed_at is None]
        if not remaining:
            wf = await self.uow.workflows.complete(task.workflow_id)
            await self._publish_event("WORKFLOW_COMPLETED", {
                "workflow_id": str(wf.id),
                "object_type": wf.object_type,
                "object_id": str(wf.object_id),
            })

        return task

    async def reject(
        self,
        task_id: uuid.UUID,
        reason: str | None = None,
    ) -> ApprovalTask | None:
        """Reject a task and cancel the workflow."""
        task = await self.uow.approval_tasks.get(task_id)
        if not task:
            return None

        task = await self.uow.approval_tasks.reject(task_id, reason)

        wf = await self.uow.workflows.cancel(task.workflow_id)
        if wf:
            await self._publish_event("WORKFLOW_REJECTED", {
                "workflow_id": str(wf.id),
                "object_type": wf.object_type,
                "object_id": str(wf.object_id),
                "reason": reason,
            })

        return task

    async def _find_template(self, object_type: str):
        """Find matching workflow template by object type."""
        try:
            return await self.uow.workflow_templates.find_by_object_type(object_type)
        except AttributeError:
            # workflow_templates repository not available
            return None

    async def _create_tasks(
        self,
        workflow_id: uuid.UUID,
        step_names: list[str],
    ) -> list[ApprovalTask]:
        """Create approval tasks for each step in the template."""
        tasks = []
        for step_name in step_names:
            task = await self.uow.approval_tasks.create({
                "workflow_id": workflow_id,
                "status": "PENDING",
                "payload": {"step": step_name},
                "step_name": step_name,
            })
            tasks.append(task)
        return tasks

    async def _publish_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Publish domain event. Uses event bus if available."""
        try:
            from app.events.event_bus import publish
            await publish(event_type, payload)
        except ImportError:
            pass  # Event system not yet available
        except Exception:
            pass  # Silently ignore event errors

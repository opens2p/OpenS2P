"""
OpenS2P – Workflow repository
==============================
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import ApprovalTask, WorkflowInstance, WorkflowStatus
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[WorkflowInstance]):
    """Tenant-scoped workflow-instance repository."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, WorkflowInstance, tenant_id=tenant_id)

    # ── lifecycle ─────────────────────────────────────────────────────────

    async def start_workflow(
        self,
        object_type: str,
        object_id: uuid.UUID,
    ) -> WorkflowInstance:
        """Create a new workflow instance in PENDING status."""
        instance = WorkflowInstance(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            object_type=object_type,
            object_id=object_id,
            status=WorkflowStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        return await self.create(instance)

    async def complete(self, workflow_id: uuid.UUID) -> WorkflowInstance | None:
        return await self.update(workflow_id, {
            "status": WorkflowStatus.COMPLETED,
        })

    async def cancel(self, workflow_id: uuid.UUID) -> WorkflowInstance | None:
        return await self.update(workflow_id, {
            "status": WorkflowStatus.CANCELLED,
        })

    # ── lookups ───────────────────────────────────────────────────────────

    async def get_with_tasks(self, workflow_id: uuid.UUID) -> WorkflowInstance | None:
        stmt = (
            self._stmt()
            .where(WorkflowInstance.id == workflow_id)
            .options(joinedload(WorkflowInstance.tasks))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_object(
        self,
        object_type: str,
        object_id: uuid.UUID,
    ) -> list[WorkflowInstance]:
        stmt = self._stmt().where(
            WorkflowInstance.object_type == object_type,
            WorkflowInstance.object_id == object_id,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_pending(self) -> list[WorkflowInstance]:
        stmt = self._stmt().where(
            WorkflowInstance.status == WorkflowStatus.PENDING,
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())


class ApprovalTaskRepository(BaseRepository[ApprovalTask]):
    """Repository for individual approval steps."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, ApprovalTask, tenant_id=tenant_id)

    async def list_by_approver(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ApprovalTask]:
        stmt = self._stmt().where(ApprovalTask.approver_id == user_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_pending_for(
        self,
        user_id: uuid.UUID,
    ) -> list[ApprovalTask]:
        """Tasks awaiting action from a specific user."""
        stmt = self._stmt().where(
            ApprovalTask.approver_id == user_id,
            ApprovalTask.completed_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def approve(
        self,
        task_id: uuid.UUID,
        payload: dict[str, Any] | None = None,
    ) -> ApprovalTask | None:
        return await self.update(task_id, {
            "completed_at": datetime.utcnow(),
            "status": "APPROVED",
            "payload": payload,
        })

    async def reject(
        self,
        task_id: uuid.UUID,
        reason: str | None = None,
    ) -> ApprovalTask | None:
        return await self.update(task_id, {
            "completed_at": datetime.utcnow(),
            "status": "REJECTED",
            "payload": {"reason": reason} if reason else None,
        })

    async def delegate(
        self,
        task_id: uuid.UUID,
        new_approver_id: uuid.UUID,
    ) -> ApprovalTask | None:
        return await self.update(task_id, {
            "approver_id": new_approver_id,
        })

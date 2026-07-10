from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base, WorkflowStatus


class WorkflowInstance(Base, AuditMixin):
    """Running workflow for a business object (PR / PO / Contract …)."""

    __tablename__ = "workflow_instances"

    object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    object_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus), nullable=False, server_default=WorkflowStatus.PENDING.value,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    workflow_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_step: Mapped[int | None] = mapped_column(nullable=True)
    wf_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # -- relationships -------------------------------------------------------
    tasks: Mapped[List["ApprovalTask"]] = relationship(
        "ApprovalTask", back_populates="workflow", cascade="all, delete-orphan",
    )


class ApprovalTask(Base, AuditMixin):
    """Individual approval step inside a workflow."""

    __tablename__ = "approval_tasks"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True,
    )
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    status: Mapped[str | None] = mapped_column(String(50))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    step_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comments: Mapped[str | None] = mapped_column(nullable=True)

    # -- relationships -------------------------------------------------------
    workflow: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", back_populates="tasks",
    )

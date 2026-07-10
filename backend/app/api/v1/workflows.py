"""
OpenS2P – Workflow API endpoints
==================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.serialization import safe_validate
from app.schemas.workflow import (
    ApproveRequest,
    EscalationRequest,
    RejectRequest,
    WorkflowStartRequest,
    WorkflowResponse,
    WorkflowHistoryResponse,
    ApprovalTaskResponse,
)
from app.services.workflow_service import WorkflowService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/workflows", tags=["Workflow"])


@router.post("", response_model=ApiResponse[WorkflowResponse], status_code=201)
async def start_workflow(
    body: WorkflowStartRequest,
    _: None = Depends(require_permission(perm.WORKFLOW_START)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow, actor_id=auth.user_id)
        wf = await svc.start_workflow(body.object_type, body.object_id)
        # Re-fetch with tasks eagerly loaded
        wf = await uow.workflows.get_with_tasks(wf.id)
        await uow.commit()
        return ApiResponse(
            data=await safe_validate(WorkflowResponse, wf),
            message="Workflow started",
        )


@router.get("/{workflow_id}", response_model=ApiResponse[WorkflowResponse])
async def get_workflow(
    workflow_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.WORKFLOW_START)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        wf = await uow.workflows.get_with_tasks(workflow_id)
        if wf is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return ApiResponse(data=await safe_validate(WorkflowResponse, wf))


@router.get("/tasks/pending", response_model=ApiResponse[list[ApprovalTaskResponse]])
async def pending_tasks(
    user_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.WORKFLOW_DECIDE)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow)
        tasks = await svc.get_pending_tasks(user_id)
        return ApiResponse(
            data=[await safe_validate(ApprovalTaskResponse, t) for t in tasks],
        )


@router.post("/tasks/{task_id}/approve", response_model=ApiResponse[ApprovalTaskResponse])
async def approve_task(
    task_id: uuid.UUID,
    body: ApproveRequest = ApproveRequest(),
    _: None = Depends(require_permission(perm.WORKFLOW_DECIDE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow, actor_id=auth.user_id)
        result = await svc.approve_task(task_id, body.payload)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await uow.commit()
        return ApiResponse(
            data=await safe_validate(ApprovalTaskResponse, result),
            message="Task approved",
        )


@router.post("/tasks/{task_id}/reject", response_model=ApiResponse[ApprovalTaskResponse])
async def reject_task(
    task_id: uuid.UUID,
    body: RejectRequest = RejectRequest(),
    _: None = Depends(require_permission(perm.WORKFLOW_DECIDE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow, actor_id=auth.user_id)
        result = await svc.reject_task(task_id, body.reason)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await uow.commit()
        return ApiResponse(
            data=await safe_validate(ApprovalTaskResponse, result),
            message="Task rejected",
        )


@router.get("/history/{object_type}/{object_id}", response_model=ApiResponse[list[WorkflowResponse]])
async def get_workflow_history(
    object_type: str,
    object_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.WORKFLOW_START)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow)
        history = await svc.get_workflow_history(object_type, object_id)
        return ApiResponse(
            data=[await safe_validate(WorkflowResponse, wf) for wf in history],
        )


@router.post("/tasks/{task_id}/escalate", response_model=ApiResponse[ApprovalTaskResponse])
async def escalate_task(
    task_id: uuid.UUID,
    body: EscalationRequest,
    _: None = Depends(require_permission(perm.WORKFLOW_ESCALATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow, actor_id=auth.user_id)
        result = await uow.approval_tasks.delegate(task_id, body.new_approver_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await uow.commit()
        return ApiResponse(
            data=await safe_validate(ApprovalTaskResponse, result),
            message="Task escalated",
        )

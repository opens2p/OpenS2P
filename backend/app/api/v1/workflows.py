"""
OpenS2P – Workflow API endpoints
==================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.workflow import (
    DecisionRequest,
    EscalationRequest,
    WorkflowStartRequest,
    WorkflowResponse,
    ApprovalTaskResponse,
)
from app.services.workflow_service import WorkflowService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/workflows", tags=["Workflow"])


@router.post("", response_model=ApiResponse[WorkflowResponse], status_code=201)
async def start_workflow(
    body: WorkflowStartRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow)
        wf = await svc.start_workflow(body.object_type, body.object_id)
        await uow.commit()
        return ApiResponse(data=WorkflowResponse.model_validate(wf), message="Workflow started")


@router.get("/{workflow_id}", response_model=ApiResponse[WorkflowResponse])
async def get_workflow(
    workflow_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        wf = await uow.workflows.get_with_tasks(workflow_id)
        if wf is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return ApiResponse(data=WorkflowResponse.model_validate(wf))


@router.get("/tasks/pending", response_model=ApiResponse[list[ApprovalTaskResponse]])
async def pending_tasks(
    user_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow)
        tasks = await svc.get_pending_tasks(user_id)
        return ApiResponse(data=[ApprovalTaskResponse.model_validate(t) for t in tasks])


@router.post("/tasks/{task_id}/decide", response_model=ApiResponse[ApprovalTaskResponse])
async def decide_task(
    task_id: uuid.UUID,
    body: DecisionRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow)
        result = await svc.process_decision(task_id, body.decision, body.payload)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await uow.commit()
        return ApiResponse(data=ApprovalTaskResponse.model_validate(result), message="Decision recorded")


@router.post("/tasks/{task_id}/escalate", response_model=ApiResponse[ApprovalTaskResponse])
async def escalate_task(
    task_id: uuid.UUID,
    body: EscalationRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = WorkflowService(uow)
        result = await svc.escalate(task_id, body.new_approver_id, body.reason)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await uow.commit()
        return ApiResponse(data=ApprovalTaskResponse.model_validate(result), message="Task escalated")

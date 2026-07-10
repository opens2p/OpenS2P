"""
OpenS2P – AI Copilot API
==========================
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.schemas.common import ApiResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.ai.copilot.service import CopilotService

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []

@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def chat(
    body: ChatRequest,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = CopilotService(uow=uow)
        result = await svc.chat(body.message)
        return ApiResponse(data=ChatResponse(**result))

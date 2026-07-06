"""
OpenS2P – Audit API endpoints
===============================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.models import User
from app.schemas.common import ApiResponse
from app.services.audit_service import AuditService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/audit", tags=["Audit"])


def _build_changes(old: dict | None, new: dict | None) -> list[dict]:
    """Build a structured list of what changed."""
    changes: list[dict] = []
    if not old or not new:
        return changes
    for key in set(list(old.keys()) + list(new.keys())):
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            changes.append({"field": key, "old": old_val, "new": new_val})
    return changes


async def _enrich_events(events: list, uow: UnitOfWork) -> list[dict]:
    """Attach actor usernames to audit events."""
    result = []
    for e in events:
        actor = None
        if e.created_by:
            user = await uow.users.get(e.created_by)
            actor = user.username if user else None
        result.append({
            "id": str(e.id),
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": str(e.entity_id),
            "actor": actor,
            "changes": _build_changes(e.old_values, e.new_values),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    return result


@router.get("/{entity_type}/{entity_id}")
async def get_entity_audit(
    entity_type: str,
    entity_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Full change history for a specific business object."""
    async with uow:
        svc = AuditService(uow)
        events = await svc.get_history(entity_type, entity_id, skip=skip, limit=limit)
        return ApiResponse(data=await _enrich_events(events, uow))


@router.get("/recent")
async def get_recent_audit(
    limit: int = 20,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Most recent audit events across all entities."""
    async with uow:
        svc = AuditService(uow)
        events = await svc.get_timeline(skip=0, limit=limit)
        return ApiResponse(data=await _enrich_events(events, uow))


@router.get("/user/{user_id}")
async def get_user_audit(
    user_id: uuid.UUID,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Audit events authored by a specific user."""
    async with uow:
        svc = AuditService(uow)
        all_events = await svc.get_timeline(skip=0, limit=200)
        filtered = [e for e in all_events if e.created_by == user_id][:limit]
        return ApiResponse(data=await _enrich_events(filtered, uow))

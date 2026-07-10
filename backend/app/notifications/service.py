"""
OpenS2P – In-App Notification Service
=======================================
Sends notifications for approval requests, status changes, etc.
Listens to domain events and creates user-facing notifications.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.events.event_bus import publish, subscribe


class NotificationService:
    """Creates and manages in-app notifications."""

    def __init__(self, uow=None) -> None:
        self.uow = uow

    async def notify(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str = "INFO",
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Create an in-app notification."""
        notification: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "reference_type": reference_type,
            "reference_id": str(reference_id) if reference_id else None,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.uow and hasattr(self.uow, "notifications"):
            await self.uow.notifications.create(notification)

        # Also publish as event for other consumers
        await publish("NOTIFICATION_CREATED", notification)

        return notification


# ── Event Handlers ────────────────────────────────────────────────────────


async def on_workflow_started(event: dict[str, Any]) -> None:
    """Send notification when a workflow starts."""
    payload = event["payload"]
    print(
        f"[Notification] Workflow started: "
        f"{payload.get('object_type')} #{payload.get('object_id')}"
    )


async def on_approval_needed(event: dict[str, Any]) -> None:
    """Send notification when approval is needed."""
    payload = event["payload"]
    print(
        f"[Notification] Approval needed: "
        f"{payload.get('step')} for {payload.get('object_type')}"
    )


async def on_workflow_completed(event: dict[str, Any]) -> None:
    """Send notification when a workflow completes."""
    payload = event["payload"]
    print(
        f"[Notification] Workflow completed: "
        f"{payload.get('object_type')} #{payload.get('object_id')}"
    )

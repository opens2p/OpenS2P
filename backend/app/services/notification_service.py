"""
OpenS2P – Notification Service
================================
Placeholder for out-of-band notifications (email, Slack, in-app).

In production this will integrate with:
* transactional email provider (SendGrid / SES)
* Slack / Teams webhooks
* in-app notification bus
"""

from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import Any


class NotificationChannel(PyEnum):
    EMAIL = "email"
    IN_APP = "in_app"
    SLACK = "slack"


class NotificationPriority(PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class NotificationService:
    """Send notifications to users about procurement events.

    Currently a placeholder — all methods log to stdout.
    """

    async def send(
        self,
        *,
        recipient_id: uuid.UUID,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        title: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send a notification to a user.

        TODO: wire up to real email / Slack / in-app channel.
        """
        print(
            f"[NOTIFICATION] {priority.value.upper()} | "
            f"to={recipient_id} | "
            f"channel={channel.value} | "
            f"title={title}"
        )

    async def notify_approver(
        self,
        approver_id: uuid.UUID,
        task_type: str,
        task_id: uuid.UUID,
    ) -> None:
        """Alert an approver about a pending approval task."""
        await self.send(
            recipient_id=approver_id,
            channel=NotificationChannel.EMAIL,
            title=f"Approval Required: {task_type}",
            body=f"A new {task_type} ({task_id}) requires your review.",
            priority=NotificationPriority.HIGH,
        )

    async def notify_supplier_status_change(
        self,
        supplier_name: str,
        new_status: str,
    ) -> None:
        """Notify relevant stakeholders about supplier status changes."""
        print(
            f"[NOTIFICATION] Supplier '{supplier_name}' status changed to {new_status}"
        )

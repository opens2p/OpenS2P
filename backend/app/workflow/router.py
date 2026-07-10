"""
OpenS2P – Smart Workflow Routing
==================================
Determines the correct approver for each step based on business rules,
org hierarchy, and context.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.workflow.rules import DEFAULT_RULES, Rule, resolve_approver


async def determine_approver(
    step_name: str,
    context: dict[str, Any],
    custom_rules: list[Rule] | None = None,
    default_approver_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    """
    Determine who should approve the current step.

    Uses rules engine to match the step + context to an approver role.
    Then looks up a user with that role in the current tenant.

    Returns None if no approver can be determined (will need manual assignment).
    """
    all_rules = list(DEFAULT_RULES)
    if custom_rules:
        all_rules.extend(custom_rules)

    approver_role = await resolve_approver(all_rules, context)
    # In production, look up a user with this role in the tenant
    # For now, return default
    return default_approver_id


def build_context(
    object_type: str,
    object_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a context dict for rule evaluation from an object's data.
    """
    context: dict[str, Any] = {
        "object_type": object_type,
    }
    if object_data:
        context.update(object_data)
    return context

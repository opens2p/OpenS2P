"""
OpenS2P – Rule-Based Approval Routing
======================================
Maps business rules to approver roles based on conditions.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.workflow.conditions import evaluate_condition


class Rule:
    """A single approval rule linking a condition to an approver role."""

    def __init__(
        self,
        rule_id: str,
        condition: str,
        approver_role: str,
        priority: int = 0,
        description: str = "",
    ) -> None:
        self.rule_id = rule_id
        self.condition = condition
        self.approver_role = approver_role
        self.priority = priority
        self.description = description

    def matches(self, context: dict[str, Any]) -> bool:
        """Check if this rule's condition matches the context."""
        return evaluate_condition(self.condition, context)


async def resolve_approver(
    rules: list[Rule],
    context: dict[str, Any],
    default_role: str = "PROCUREMENT_MANAGER",
) -> str:
    """
    Find the best matching approver role for a given context.

    Rules are evaluated in priority order. The first matching rule
    determines the approver role. If no rule matches, returns default.
    """
    sorted_rules = sorted(rules, key=lambda r: -r.priority)
    for rule in sorted_rules:
        if rule.matches(context):
            return rule.approver_role
    return default_role


# Built-in approval rules
DEFAULT_RULES: list[Rule] = [
    Rule(
        "high_value",
        "amount > 100000",
        "FINANCE_USER",
        priority=100,
        description="High value purchases need finance approval",
    ),
    Rule(
        "medium_value",
        "amount > 10000",
        "PROCUREMENT_MANAGER",
        priority=50,
        description="Medium value needs procurement manager",
    ),
    Rule(
        "high_risk_supplier",
        "supplier_risk == HIGH",
        "LEGAL_REVIEW",
        priority=80,
        description="High risk suppliers need legal review",
    ),
    Rule(
        "it_category",
        "category == IT",
        "IT_MANAGER",
        priority=60,
        description="IT purchases need IT manager approval",
    ),
]

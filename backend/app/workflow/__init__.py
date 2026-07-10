"""
OpenS2P – Workflow Engine
==========================
Core workflow orchestration: engine, conditions, rules, and routing.
"""

from .engine import WorkflowEngine
from .conditions import evaluate_condition
from .rules import Rule, resolve_approver, DEFAULT_RULES
from .router import determine_approver, build_context

__all__ = [
    "WorkflowEngine",
    "evaluate_condition",
    "Rule",
    "resolve_approver",
    "DEFAULT_RULES",
    "determine_approver",
    "build_context",
]

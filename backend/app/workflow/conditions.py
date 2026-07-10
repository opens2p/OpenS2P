"""
OpenS2P – Workflow Condition Evaluator
=======================================
Evaluates rules like: amount > 100000, department == "IT", supplier_risk == "HIGH"

Uses simple parsing — no eval() for security.
"""

from __future__ import annotations

import json
import operator
from typing import Any


def evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    """
    Evaluate a condition string against a context dict.

    Supports:
    - amount > 100000
    - department == "IT"
    - supplier_risk == "HIGH"
    - category in ["IT", "SOFTWARE"]
    """
    condition = condition.strip()

    # Parse operator — sorted by length so >= matches before >
    ops: list[tuple[str, Any]] = [
        (">=", operator.ge),
        ("<=", operator.le),
        ("!=", operator.ne),
        ("==", operator.eq),
        (">", operator.gt),
        ("<", operator.lt),
    ]

    # Check for "in" operator separately
    if " in " in condition:
        parts = condition.split(" in ", 1)
        if len(parts) == 2:
            left = parts[0].strip()
            right = parts[1].strip()

            ctx_value = _resolve_path(context, left)
            if ctx_value is None:
                return False

            # Parse right side as a list
            if right.startswith("[") and right.endswith("]"):
                try:
                    right_value = json.loads(right.replace("'", '"'))
                except (json.JSONDecodeError, ValueError):
                    right_value = [
                        x.strip().strip("'\"").strip()
                        for x in right.strip("[]").split(",")
                    ]
            else:
                right_value = [right.strip().strip("'\"").strip()]

            try:
                return ctx_value in right_value
            except (TypeError, ValueError):
                return False

    for op_str, op_func in ops:
        if op_str in condition:
            parts = condition.split(op_str, 1)
            if len(parts) != 2:
                continue

            left = parts[0].strip()
            right = parts[1].strip().strip('"').strip("'")

            # Get value from context
            ctx_value = _resolve_path(context, left)
            if ctx_value is None:
                return False

            # Parse right side
            right_value = _parse_value(right)

            try:
                return bool(op_func(ctx_value, right_value))
            except (TypeError, ValueError):
                return False

    return True


def _parse_value(raw: str) -> Any:
    """Parse a string value into its proper Python type."""
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.lower() == "none":
        return None
    # Check for numeric values
    try:
        if "." in raw or "e" in raw.lower():
            return float(raw)
        return int(raw)
    except (ValueError, TypeError):
        pass
    return raw


def _resolve_path(context: dict, path: str) -> Any:
    """Resolve dotted path like 'supplier.risk_score' in context dict."""
    parts = path.split(".")
    value: Any = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value

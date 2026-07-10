"""
AI guardrails — safety checks for inputs and outputs.
"""
from __future__ import annotations
from typing import Any


def validate_input(prompt: str, context: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Check if input is safe to process."""
    if not prompt or not prompt.strip():
        return False, "Empty prompt"
    if len(prompt) > 10000:
        return False, "Prompt too long"
    blocked_patterns = ["ignore previous instructions", "system prompt", "admin password"]
    for pattern in blocked_patterns:
        if pattern in prompt.lower():
            return False, "Blocked content detected"
    return True, ""


def sanitize_output(output: str) -> str:
    """Remove sensitive information from AI output."""
    import re
    output = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', output)
    output = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[CARD]', output)
    return output


def mask_sensitive_context(context: dict[str, Any]) -> dict[str, Any]:
    """Mask sensitive fields before sending to AI provider."""
    masked = context.copy()
    sensitive_keys = {"password", "api_key", "secret", "token", "ssn", "ein", "tax_id"}
    for key in masked:
        if any(s in key.lower() for s in sensitive_keys):
            masked[key] = "***"
    return masked

"""
OpenS2P – AI Core
==================
Core AI abstractions: provider, prompts, and guardrails.
"""

from .provider import AIProvider
from .prompts import PROMPTS
from .guardrails import validate_input, sanitize_output, mask_sensitive_context

__all__ = [
    "AIProvider",
    "PROMPTS",
    "validate_input",
    "sanitize_output",
    "mask_sensitive_context",
]

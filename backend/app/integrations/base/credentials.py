"""
Credential management for integrations.
In production, credentials should be encrypted at rest.
"""
from __future__ import annotations
from typing import Any


def mask_credentials(credentials: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mask sensitive credential values for logging/display."""
    if not credentials:
        return None
    sensitive_keys = {"password", "api_key", "secret", "token", "client_secret"}
    masked = {}
    for k, v in credentials.items():
        if k.lower() in sensitive_keys and v:
            masked[k] = v[:4] + "****" if len(v) > 4 else "****"
        else:
            masked[k] = v
    return masked


def validate_credentials(credentials: dict[str, Any] | None, auth_type: str) -> list[str]:
    """Validate that required credential fields are present."""
    required_fields = {
        "basic": ["username", "password"],
        "api_key": ["api_key"],
        "oauth2": ["client_id", "client_secret", "token_url"],
        "certificate": ["certificate_path", "key_path"],
    }
    missing = []
    fields = required_fields.get(auth_type, [])
    for field in fields:
        if not credentials or not credentials.get(field):
            missing.append(field)
    return missing

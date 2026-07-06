"""
OpenS2P – Security
===================
Authentication (JWT), authorisation (RBAC), password hashing,
and FastAPI security dependencies.
"""

from .password import hash_password, verify_password
from .jwt import create_access_token, decode_access_token
from .permissions import (  # noqa: F401
    get_permissions,
    has_permission,
    SUPPLIER_CREATE, SUPPLIER_VIEW, SUPPLIER_UPDATE, SUPPLIER_APPROVE, SUPPLIER_BLOCK,
    CONTRACT_CREATE, CONTRACT_VIEW, CONTRACT_ACTIVATE, CONTRACT_RENEW,
    SOURCING_CREATE, SOURCING_VIEW, SOURCING_BID, SOURCING_AWARD,
    PR_CREATE, PR_VIEW, PR_APPROVE, PR_REJECT,
    PO_CREATE, PO_VIEW, PO_SEND, PO_CLOSE, PO_CANCEL,
    INVOICE_CREATE, INVOICE_VIEW, INVOICE_MATCH, INVOICE_APPROVE_PAYMENT,
    WORKFLOW_START, WORKFLOW_DECIDE, WORKFLOW_ESCALATE,
    ADMIN_HEALTH, ADMIN_STATS, ADMIN_MANAGE_USERS,
)
from .dependencies import AuthContext, require_auth, require_permission, optional_auth

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_permissions",
    "has_permission",
    "SUPPLIER_CREATE", "SUPPLIER_VIEW", "SUPPLIER_UPDATE", "SUPPLIER_APPROVE", "SUPPLIER_BLOCK",
    "CONTRACT_CREATE", "CONTRACT_VIEW", "CONTRACT_ACTIVATE", "CONTRACT_RENEW",
    "SOURCING_CREATE", "SOURCING_VIEW", "SOURCING_BID", "SOURCING_AWARD",
    "PR_CREATE", "PR_VIEW", "PR_APPROVE", "PR_REJECT",
    "PO_CREATE", "PO_VIEW", "PO_SEND", "PO_CLOSE", "PO_CANCEL",
    "INVOICE_CREATE", "INVOICE_VIEW", "INVOICE_MATCH", "INVOICE_APPROVE_PAYMENT",
    "WORKFLOW_START", "WORKFLOW_DECIDE", "WORKFLOW_ESCALATE",
    "ADMIN_HEALTH", "ADMIN_STATS", "ADMIN_MANAGE_USERS",
    "AuthContext",
    "require_auth",
    "require_permission",
    "optional_auth",
]

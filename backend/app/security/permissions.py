"""
OpenS2P – RBAC permissions
============================
Maps role names to sets of allowed actions.

Permissions are strings in the form ``<domain>.<action>``:

    supplier.create
    supplier.approve
    purchase_order.view
    invoice.match
"""

from __future__ import annotations

from typing import FrozenSet

# ── permission constants ───────────────────────────────────────────────────

# Supplier
SUPPLIER_CREATE = "supplier.create"
SUPPLIER_VIEW = "supplier.view"
SUPPLIER_UPDATE = "supplier.update"
SUPPLIER_APPROVE = "supplier.approve"
SUPPLIER_BLOCK = "supplier.block"

# Contract
CONTRACT_CREATE = "contract.create"
CONTRACT_VIEW = "contract.view"
CONTRACT_ACTIVATE = "contract.activate"
CONTRACT_RENEW = "contract.renew"

# Sourcing
SOURCING_CREATE = "sourcing.create"
SOURCING_VIEW = "sourcing.view"
SOURCING_BID = "sourcing.bid"
SOURCING_AWARD = "sourcing.award"

# Purchase Requisition
PR_CREATE = "pr.create"
PR_VIEW = "pr.view"
PR_APPROVE = "pr.approve"
PR_REJECT = "pr.reject"

# Purchase Order
PO_CREATE = "po.create"
PO_VIEW = "po.view"
PO_SEND = "po.send"
PO_CLOSE = "po.close"
PO_CANCEL = "po.cancel"

# Invoice
INVOICE_CREATE = "invoice.create"
INVOICE_VIEW = "invoice.view"
INVOICE_MATCH = "invoice.match"
INVOICE_APPROVE_PAYMENT = "invoice.approve_payment"

# Supplier – extended
SUPPLIER_DELETE = "supplier.delete"

# Contract – extended
CONTRACT_UPDATE = "contract.update"
CONTRACT_DELETE = "contract.delete"

# Purchase Requisition – extended
PR_UPDATE = "pr.update"
PR_DELETE = "pr.delete"
PR_SUBMIT = "pr.submit"

# Purchase Order – extended
PO_UPDATE = "po.update"
PO_DELETE = "po.delete"

# Invoice – extended
INVOICE_UPDATE = "invoice.update"
INVOICE_DELETE = "invoice.delete"
INVOICE_PAY = "invoice.pay"

# Workflow
WORKFLOW_START = "workflow.start"
WORKFLOW_DECIDE = "workflow.decide"
WORKFLOW_ESCALATE = "workflow.escalate"

# Admin
ADMIN_HEALTH = "admin.health"
ADMIN_STATS = "admin.stats"
ADMIN_MANAGE_USERS = "admin.manage_users"

# ── role → permissions mapping ────────────────────────────────────────────

_ROLE_PERMISSIONS: dict[str, FrozenSet[str]] = {
    "SYSTEM_ADMIN": frozenset({
        SUPPLIER_CREATE, SUPPLIER_VIEW, SUPPLIER_UPDATE, SUPPLIER_APPROVE, SUPPLIER_BLOCK, SUPPLIER_DELETE,
        CONTRACT_CREATE, CONTRACT_VIEW, CONTRACT_UPDATE, CONTRACT_ACTIVATE, CONTRACT_RENEW, CONTRACT_DELETE,
        SOURCING_CREATE, SOURCING_VIEW, SOURCING_BID, SOURCING_AWARD,
        PR_CREATE, PR_VIEW, PR_UPDATE, PR_APPROVE, PR_REJECT, PR_DELETE, PR_SUBMIT,
        PO_CREATE, PO_VIEW, PO_UPDATE, PO_SEND, PO_CLOSE, PO_CANCEL, PO_DELETE,
        INVOICE_CREATE, INVOICE_VIEW, INVOICE_UPDATE, INVOICE_MATCH, INVOICE_APPROVE_PAYMENT, INVOICE_DELETE, INVOICE_PAY,
        WORKFLOW_START, WORKFLOW_DECIDE, WORKFLOW_ESCALATE,
        ADMIN_HEALTH, ADMIN_STATS, ADMIN_MANAGE_USERS,
    }),
    "PROCUREMENT_ADMIN": frozenset({
        SUPPLIER_CREATE, SUPPLIER_VIEW, SUPPLIER_UPDATE, SUPPLIER_APPROVE, SUPPLIER_BLOCK, SUPPLIER_DELETE,
        CONTRACT_CREATE, CONTRACT_VIEW, CONTRACT_UPDATE, CONTRACT_ACTIVATE, CONTRACT_RENEW, CONTRACT_DELETE,
        SOURCING_CREATE, SOURCING_VIEW, SOURCING_BID, SOURCING_AWARD,
        PR_CREATE, PR_VIEW, PR_UPDATE, PR_APPROVE, PR_REJECT, PR_DELETE, PR_SUBMIT,
        PO_CREATE, PO_VIEW, PO_UPDATE, PO_SEND, PO_CLOSE, PO_CANCEL, PO_DELETE,
        INVOICE_CREATE, INVOICE_VIEW, INVOICE_UPDATE, INVOICE_MATCH, INVOICE_APPROVE_PAYMENT, INVOICE_DELETE, INVOICE_PAY,
        WORKFLOW_START, WORKFLOW_DECIDE, WORKFLOW_ESCALATE,
        ADMIN_HEALTH, ADMIN_STATS,
    }),
    "BUYER": frozenset({
        SUPPLIER_CREATE, SUPPLIER_VIEW, SUPPLIER_UPDATE, SUPPLIER_DELETE,
        CONTRACT_CREATE, CONTRACT_VIEW, CONTRACT_UPDATE, CONTRACT_DELETE,
        SOURCING_VIEW, SOURCING_BID,
        PR_CREATE, PR_VIEW, PR_UPDATE, PR_DELETE, PR_SUBMIT,
        PO_CREATE, PO_VIEW, PO_UPDATE, PO_SEND, PO_CLOSE, PO_DELETE,
        INVOICE_CREATE, INVOICE_VIEW, INVOICE_UPDATE, INVOICE_DELETE,
        WORKFLOW_START,
    }),
    "REQUESTER": frozenset({
        SUPPLIER_VIEW,
        PR_CREATE, PR_VIEW, PR_UPDATE, PR_SUBMIT,
        PO_VIEW,
        INVOICE_VIEW,
    }),
    "APPROVER": frozenset({
        SUPPLIER_VIEW,
        PR_VIEW, PR_APPROVE, PR_REJECT,
        PO_VIEW,
        INVOICE_VIEW,
        WORKFLOW_DECIDE, WORKFLOW_ESCALATE,
    }),
    "SUPPLIER_USER": frozenset({
        SUPPLIER_VIEW,
        SOURCING_VIEW, SOURCING_BID,
        PO_VIEW,
        INVOICE_CREATE, INVOICE_VIEW,
    }),
    "FINANCE_USER": frozenset({
        SUPPLIER_VIEW,
        CONTRACT_VIEW,
        PO_VIEW,
        INVOICE_CREATE, INVOICE_VIEW, INVOICE_UPDATE, INVOICE_MATCH, INVOICE_APPROVE_PAYMENT, INVOICE_PAY,
        WORKFLOW_DECIDE,
        ADMIN_STATS,
    }),
}


def get_permissions(roles: list[str]) -> frozenset[str]:
    """Return the union of all permissions granted by the given roles."""
    perms: set[str] = set()
    for role in roles:
        perms.update(_ROLE_PERMISSIONS.get(role, set()))
    return frozenset(perms)


def has_permission(required: str, user_roles: list[str]) -> bool:
    """Check whether *any* of the user's roles grants the required permission."""
    return required in get_permissions(user_roles)

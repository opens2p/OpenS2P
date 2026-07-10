# ---------------------------------------------------------------------------
# OpenS2P Models – Package init
# Alembic autogenerate discovers every model imported here.
# ---------------------------------------------------------------------------

from .base import Base
from .base import AuditMixin
from .base import (
    SupplierStatus,
    PRStatus,
    POStatus,
    MatchStatus,
    InvoiceStatus,
    WorkflowStatus,
    TenantStatus,
)

# Tenant domain
from .tenant import Tenant

# Security / IAM
from .user import User
from .role import Role, UserRole

# Supplier management
from .supplier import Supplier, SupplierContact, SupplierDocument

# Sourcing
from .sourcing import SourcingEvent, SupplierBid

# Document management
from .document import Document, DocumentVersion

# Contract management
from .contract import Contract

# Procurement
from .procurement import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
    PurchaseOrder,
    PurchaseOrderItem,
)

# Master data
from .master_data import Currency, Country, Category, UnitOfMeasure

# Workflow engine
from .workflow import WorkflowInstance, ApprovalTask
from .workflow_template import WorkflowTemplate

# Receiving
from .receiving import Receipt

# Invoice
from .invoice import Invoice

# AI intelligence
from .ai import AIRecommendation

# Audit
from .audit import AuditEvent

# AI Governance
from .ai_execution import AIExecution
from .ai_governance import AIPrompt, AIRequest, AIFeedback

# Integration
from .integration import (
    IntegrationConnection,
    IntegrationRun,
    IntegrationLog,
    FieldMapping,
    ExternalReference,
)

# Analytics
from .analytics import (
    KPIDefinition,
    KPISnapshot,
    DashboardConfig,
    SavedReport,
    ReportExecution,
)

__all__ = [
    # base / mixin
    "Base",
    "AuditMixin",
    # enums
    "SupplierStatus",
    "PRStatus",
    "POStatus",
    "MatchStatus",
    "InvoiceStatus",
    "WorkflowStatus",
    "TenantStatus",
    # tenant
    "Tenant",
    # security
    "User",
    "Role",
    "UserRole",
    # supplier
    "Supplier",
    "SupplierContact",
    "SupplierDocument",
    # sourcing
    "SourcingEvent",
    "SupplierBid",
    # document management
    "Document",
    "DocumentVersion",
    # contract
    "Contract",
    # procurement
    "PurchaseRequisition",
    "PurchaseRequisitionItem",
    "PurchaseOrder",
    "PurchaseOrderItem",
    # receiving
    "Receipt",
    # invoice
    "Invoice",
    # workflow
    "WorkflowInstance",
    "ApprovalTask",
    # master data
    "Currency",
    "Country",
    "Category",
    "UnitOfMeasure",
    # workflow template
    "WorkflowTemplate",
    # ai
    "AIRecommendation",
    # audit
    "AuditEvent",
    # ai governance
    "AIExecution",
    "AIPrompt",
    "AIRequest",
    "AIFeedback",
    # integration
    "IntegrationConnection",
    "IntegrationRun",
    "IntegrationLog",
    "FieldMapping",
    "ExternalReference",
    # analytics
    "KPIDefinition",
    "KPISnapshot",
    "DashboardConfig",
    "SavedReport",
    "ReportExecution",
]

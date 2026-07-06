"""
OpenS2P – Pydantic schemas (DTOs)
===================================
Request / response models for the REST API layer.

Not to be confused with SQLAlchemy ORM models — these are
the public contract between clients and the platform.
"""

from .common import (
    PaginationParams,
    PaginatedResponse,
    ApiResponse,
    ApiError,
)
from .supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierSummary,
)
from .contract import (
    ContractCreate,
    ContractUpdate,
    ContractRenew,
    ContractResponse,
)
from .sourcing import (
    SourcingEventCreate,
    SourcingEventResponse,
    BidCreate,
    BidResponse,
    AwardRequest,
)
from .purchase_requisition import (
    PurchaseRequisitionCreate,
    PurchaseRequisitionItemCreate,
    PurchaseRequisitionResponse,
    PurchaseRequisitionItemResponse,
)
from .purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderResponse,
    PurchaseOrderItemResponse,
)
from .invoice import (
    InvoiceCreate,
    InvoiceResponse,
    MatchAction,
    PaymentApproval,
)
from .workflow import (
    WorkflowStartRequest,
    DecisionRequest,
    EscalationRequest,
    ApprovalTaskResponse,
    WorkflowResponse,
)
from .user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    RoleResponse,
    RoleAssignment,
)

__all__ = [
    # common
    "PaginationParams",
    "PaginatedResponse",
    "ApiResponse",
    "ApiError",
    # supplier
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    "SupplierSummary",
    # contract
    "ContractCreate",
    "ContractUpdate",
    "ContractRenew",
    "ContractResponse",
    # sourcing
    "SourcingEventCreate",
    "SourcingEventResponse",
    "BidCreate",
    "BidResponse",
    "AwardRequest",
    # purchase requisition
    "PurchaseRequisitionCreate",
    "PurchaseRequisitionItemCreate",
    "PurchaseRequisitionResponse",
    "PurchaseRequisitionItemResponse",
    # purchase order
    "PurchaseOrderCreate",
    "PurchaseOrderItemCreate",
    "PurchaseOrderResponse",
    "PurchaseOrderItemResponse",
    # invoice
    "InvoiceCreate",
    "InvoiceResponse",
    "MatchAction",
    "PaymentApproval",
    # workflow
    "WorkflowStartRequest",
    "DecisionRequest",
    "EscalationRequest",
    "ApprovalTaskResponse",
    "WorkflowResponse",
    # user
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "RoleResponse",
    "RoleAssignment",
]

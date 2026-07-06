"""
OpenS2P – Repositories
======================
Data-access layer separating business logic from SQLAlchemy.

Usage::

    repo = SupplierRepository(session, tenant_id=tenant_id)
    supplier = await repo.get(supplier_id)
"""

from .base import BaseRepository
from .tenant_repository import TenantRepository
from .user_repository import UserRepository
from .supplier_repository import SupplierRepository
from .contract_repository import ContractRepository
from .sourcing_repository import SourcingEventRepository, SupplierBidRepository
from .purchase_requisition_repository import (
    PurchaseRequisitionRepository,
    PurchaseRequisitionItemRepository,
)
from .purchase_order_repository import PurchaseOrderRepository, PurchaseOrderItemRepository
from .receiving_repository import ReceiptRepository
from .invoice_repository import InvoiceRepository
from .workflow_repository import WorkflowRepository, ApprovalTaskRepository
from .audit_repository import AuditRepository

__all__ = [
    "BaseRepository",
    "TenantRepository",
    "UserRepository",
    "SupplierRepository",
    "ContractRepository",
    "SourcingEventRepository",
    "SupplierBidRepository",
    "PurchaseRequisitionRepository",
    "PurchaseRequisitionItemRepository",
    "PurchaseOrderRepository",
    "PurchaseOrderItemRepository",
    "ReceiptRepository",
    "InvoiceRepository",
    "WorkflowRepository",
    "ApprovalTaskRepository",
    "AuditRepository",
]

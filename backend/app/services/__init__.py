"""
OpenS2P – Services
===================
Business-logic layer.  Every public method encapsulates a complete
procurement operation (possibly spanning multiple repositories & tables).

Usage::

    async with UnitOfWork(session, tenant_id=tenant_id) as uow:
        service = SupplierService(uow, actor_id=user_id)
        supplier = await service.approve_supplier(supplier_id)
        await uow.commit()
"""

from .uow import UnitOfWork
from .supplier_service import SupplierService
from .contract_service import ContractService
from .sourcing_service import SourcingService
from .purchase_requisition_service import PurchaseRequisitionService
from .purchase_order_service import PurchaseOrderService
from .receiving_service import ReceivingService
from .invoice_service import InvoiceService
from .workflow_service import WorkflowService
from .audit_service import AuditService
from .notification_service import NotificationService, NotificationChannel, NotificationPriority
from .ai_service import AIService

__all__ = [
    "UnitOfWork",
    "SupplierService",
    "ContractService",
    "SourcingService",
    "PurchaseRequisitionService",
    "PurchaseOrderService",
    "ReceivingService",
    "InvoiceService",
    "WorkflowService",
    "AuditService",
    "NotificationService",
    "NotificationChannel",
    "NotificationPriority",
    "AIService",
]

"""
OpenS2P – Unit of Work
=======================
Coordinates multiple repositories within a single database transaction.

Usage::

    async with UnitOfWork(session) as uow:
        supplier = await uow.suppliers.get(supplier_id)
        await uow.suppliers.update(supplier_id, {"status": SupplierStatus.APPROVED})
        await uow.audit.log(event_type="SUPPLIER_APPROVED", ...)
        await uow.workflows.start(...)
        await uow.commit()   # single commit for all changes
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    ApprovalTaskRepository,
    AuditRepository,
    ContractRepository,
    InvoiceRepository,
    PurchaseOrderRepository,
    PurchaseOrderItemRepository,
    PurchaseRequisitionItemRepository,
    PurchaseRequisitionRepository,
    ReceiptRepository,
    SourcingEventRepository,
    SupplierBidRepository,
    SupplierRepository,
    TenantRepository,
    UserRepository,
    WorkflowRepository,
)


@dataclass
class UnitOfWork:
    """Aggregates all domain repositories under a single session.

    Call ``commit()`` explicitly; if the context manager exits without a
    prior commit the transaction is rolled back.
    """

    session: AsyncSession
    tenant_id: uuid.UUID | None = None

    # repositories (lazy-initialised on first access)
    tenants: TenantRepository = field(init=False)
    users: UserRepository = field(init=False)
    suppliers: SupplierRepository = field(init=False)
    contracts: ContractRepository = field(init=False)
    sourcing_events: SourcingEventRepository = field(init=False)
    supplier_bids: SupplierBidRepository = field(init=False)
    purchase_requisitions: PurchaseRequisitionRepository = field(init=False)
    purchase_requisition_items: PurchaseRequisitionItemRepository = field(init=False)
    purchase_orders: PurchaseOrderRepository = field(init=False)
    purchase_order_items: PurchaseOrderItemRepository = field(init=False)
    receipts: ReceiptRepository = field(init=False)
    invoices: InvoiceRepository = field(init=False)
    workflows: WorkflowRepository = field(init=False)
    approval_tasks: ApprovalTaskRepository = field(init=False)
    audit: AuditRepository = field(init=False)

    def __post_init__(self) -> None:
        tid = self.tenant_id
        self.tenants = TenantRepository(self.session)
        self.users = UserRepository(self.session, tid)
        self.suppliers = SupplierRepository(self.session, tid)
        self.contracts = ContractRepository(self.session, tid)
        self.sourcing_events = SourcingEventRepository(self.session, tid)
        self.supplier_bids = SupplierBidRepository(self.session, tid)
        self.purchase_requisitions = PurchaseRequisitionRepository(self.session, tid)
        self.purchase_requisition_items = PurchaseRequisitionItemRepository(self.session, tid)
        self.purchase_orders = PurchaseOrderRepository(self.session, tid)
        self.purchase_order_items = PurchaseOrderItemRepository(self.session, tid)
        self.receipts = ReceiptRepository(self.session, tid)
        self.invoices = InvoiceRepository(self.session, tid)
        self.workflows = WorkflowRepository(self.session, tid)
        self.approval_tasks = ApprovalTaskRepository(self.session, tid)
        self.audit = AuditRepository(self.session, tid)

    async def commit(self) -> None:
        """Commit all pending changes in the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Discard all pending changes."""
        await self.session.rollback()

    async def flush(self) -> None:
        """Flush pending changes to the database without committing."""
        await self.session.flush()

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if exc_type is None:
            # If the caller already committed, a second commit is a no-op
            await self.session.commit()
        else:
            await self.session.rollback()

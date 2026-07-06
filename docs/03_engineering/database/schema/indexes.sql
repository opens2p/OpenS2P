-- ==========================================================
-- OpenS2P Database Index Strategy
-- Version : 1.0
-- Database: PostgreSQL
-- ==========================================================


-- ==========================================================
-- TENANT
-- ==========================================================

CREATE INDEX idx_tenants_code
ON tenants(tenant_code);



-- ==========================================================
-- USERS
-- ==========================================================

CREATE INDEX idx_users_tenant
ON users(tenant_id);


CREATE UNIQUE INDEX idx_users_email_tenant
ON users(tenant_id, email);



-- ==========================================================
-- ROLES
-- ==========================================================

CREATE INDEX idx_roles_tenant
ON roles(tenant_id);


CREATE INDEX idx_user_roles_user
ON user_roles(user_id);



-- ==========================================================
-- SUPPLIER MANAGEMENT
-- ==========================================================


CREATE INDEX idx_supplier_tenant
ON suppliers(tenant_id);


CREATE INDEX idx_supplier_number
ON suppliers(tenant_id, supplier_number);


CREATE INDEX idx_supplier_status
ON suppliers(status);


CREATE INDEX idx_supplier_contacts_supplier
ON supplier_contacts(supplier_id);


CREATE INDEX idx_supplier_documents_supplier
ON supplier_documents(supplier_id);



-- ==========================================================
-- SOURCING
-- ==========================================================


CREATE INDEX idx_sourcing_events_tenant
ON sourcing_events(tenant_id);


CREATE INDEX idx_sourcing_status
ON sourcing_events(status);


CREATE INDEX idx_supplier_bids_event
ON supplier_bids(event_id);


CREATE INDEX idx_supplier_bids_supplier
ON supplier_bids(supplier_id);



-- ==========================================================
-- CONTRACTS
-- ==========================================================


CREATE INDEX idx_contract_tenant
ON contracts(tenant_id);


CREATE INDEX idx_contract_supplier
ON contracts(supplier_id);


CREATE INDEX idx_contract_number
ON contracts(contract_number);



-- ==========================================================
-- PURCHASE REQUISITION
-- ==========================================================


CREATE INDEX idx_pr_tenant
ON purchase_requisitions(tenant_id);


CREATE INDEX idx_pr_requester
ON purchase_requisitions(requester_id);


CREATE INDEX idx_pr_status
ON purchase_requisitions(status);


CREATE INDEX idx_pr_items_header
ON purchase_requisition_items(requisition_id);



-- ==========================================================
-- PURCHASE ORDER
-- ==========================================================


CREATE INDEX idx_po_tenant
ON purchase_orders(tenant_id);


CREATE INDEX idx_po_supplier
ON purchase_orders(supplier_id);


CREATE INDEX idx_po_number
ON purchase_orders(po_number);


CREATE INDEX idx_po_items_header
ON purchase_order_items(po_id);



-- ==========================================================
-- RECEIVING
-- ==========================================================


CREATE INDEX idx_receipt_po
ON receipts(po_id);



-- ==========================================================
-- INVOICE
-- ==========================================================


CREATE INDEX idx_invoice_po
ON invoices(po_id);


CREATE INDEX idx_invoice_number
ON invoices(invoice_number);


CREATE INDEX idx_invoice_match_status
ON invoices(match_status);



-- ==========================================================
-- WORKFLOW
-- ==========================================================


CREATE INDEX idx_workflow_object
ON workflow_instances(object_type, object_id);


CREATE INDEX idx_approval_workflow
ON approval_tasks(workflow_id);


CREATE INDEX idx_approval_user
ON approval_tasks(approver_id);



-- ==========================================================
-- AI
-- ==========================================================


CREATE INDEX idx_ai_object
ON ai_recommendations(object_type, object_id);


CREATE INDEX idx_ai_json
ON ai_recommendations USING GIN(recommendation);



-- END
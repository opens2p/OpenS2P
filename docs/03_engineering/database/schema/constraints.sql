-- ==========================================================
-- OpenS2P Database Constraints
-- Version : 1.0
-- ==========================================================


-- ==========================================================
-- TENANT
-- ==========================================================


ALTER TABLE tenants
ADD CONSTRAINT chk_tenant_status
CHECK (
status IN 
(
'ACTIVE',
'INACTIVE',
'SUSPENDED'
)
);



-- ==========================================================
-- SUPPLIER
-- ==========================================================


ALTER TABLE suppliers
ADD CONSTRAINT chk_supplier_status
CHECK (
status IN
(
'DRAFT',
'INVITED',
'REGISTERED',
'APPROVED',
'BLOCKED'
)
);



ALTER TABLE suppliers
ADD CONSTRAINT chk_supplier_risk
CHECK (
risk_score >=0
AND
risk_score <=100
);



-- ==========================================================
-- SOURCING
-- ==========================================================


ALTER TABLE sourcing_events
ADD CONSTRAINT chk_event_type
CHECK(
event_type IN
(
'RFQ',
'RFP',
'AUCTION'
)
);



-- ==========================================================
-- PURCHASE REQUISITION
-- ==========================================================


ALTER TABLE purchase_requisitions
ADD CONSTRAINT chk_pr_status
CHECK(
status IN
(
'DRAFT',
'SUBMITTED',
'APPROVED',
'REJECTED',
'ORDERED'
)
);



-- ==========================================================
-- PURCHASE ORDER
-- ==========================================================


ALTER TABLE purchase_orders
ADD CONSTRAINT chk_po_status
CHECK(
status IN
(
'CREATED',
'SENT',
'CONFIRMED',
'CLOSED',
'CANCELLED'
)
);



-- ==========================================================
-- INVOICE
-- ==========================================================


ALTER TABLE invoices
ADD CONSTRAINT chk_invoice_match
CHECK(
match_status IN
(
'PENDING',
'MATCHED',
'EXCEPTION'
)
);



-- ==========================================================
-- AMOUNT VALIDATION
-- ==========================================================


ALTER TABLE purchase_requisition_items
ADD CONSTRAINT chk_pr_quantity
CHECK(quantity >=0);



ALTER TABLE purchase_order_items
ADD CONSTRAINT chk_po_quantity
CHECK(quantity >=0);



ALTER TABLE invoices
ADD CONSTRAINT chk_invoice_amount
CHECK(amount >=0);



-- ==========================================================
-- AI
-- ==========================================================


ALTER TABLE ai_recommendations
ADD CONSTRAINT chk_ai_confidence
CHECK(
confidence >=0
AND
confidence <=100
);



-- END
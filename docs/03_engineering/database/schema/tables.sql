-- ==========================================================
-- OpenS2P Database Schema
-- Version : 1.0
-- Database: PostgreSQL
-- ==========================================================


-- Required extensions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ==========================================================
-- 1. TENANT MANAGEMENT
-- ==========================================================


CREATE TABLE tenants (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,

    status VARCHAR(30) DEFAULT 'ACTIVE',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    updated_at TIMESTAMP,
    updated_by UUID,

    is_active BOOLEAN DEFAULT TRUE
);



-- ==========================================================
-- USERS / SECURITY
-- ==========================================================


CREATE TABLE users (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID NOT NULL,

    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    status VARCHAR(30),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,

    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT fk_user_tenant
        FOREIGN KEY(tenant_id)
        REFERENCES tenants(id)

);



CREATE TABLE roles (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID,

    role_name VARCHAR(100) NOT NULL,

    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);



CREATE TABLE user_roles (

    user_id UUID,
    role_id UUID,

    PRIMARY KEY(user_id, role_id),

    FOREIGN KEY(user_id)
        REFERENCES users(id),

    FOREIGN KEY(role_id)
        REFERENCES roles(id)

);



-- ==========================================================
-- SUPPLIER MANAGEMENT
-- ==========================================================


CREATE TABLE suppliers (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID NOT NULL,

    supplier_number VARCHAR(50),
    supplier_name VARCHAR(255) NOT NULL,

    status VARCHAR(50),

    risk_score NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,

    is_active BOOLEAN DEFAULT TRUE,


    FOREIGN KEY(tenant_id)
        REFERENCES tenants(id)

);



CREATE TABLE supplier_contacts (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    supplier_id UUID NOT NULL,

    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),

    FOREIGN KEY(supplier_id)
        REFERENCES suppliers(id)

);



CREATE TABLE supplier_documents (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    supplier_id UUID NOT NULL,

    document_name VARCHAR(255),
    document_url TEXT,

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    FOREIGN KEY(supplier_id)
        REFERENCES suppliers(id)

);



-- ==========================================================
-- SOURCING
-- ==========================================================


CREATE TABLE sourcing_events (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID NOT NULL,

    event_name VARCHAR(255),

    event_type VARCHAR(50),

    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    FOREIGN KEY(tenant_id)
        REFERENCES tenants(id)

);



CREATE TABLE supplier_bids (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    event_id UUID NOT NULL,

    supplier_id UUID NOT NULL,

    bid_amount NUMERIC(15,2),

    submitted_at TIMESTAMP,


    FOREIGN KEY(event_id)
        REFERENCES sourcing_events(id),


    FOREIGN KEY(supplier_id)
        REFERENCES suppliers(id)

);



-- ==========================================================
-- CONTRACT MANAGEMENT
-- ==========================================================


CREATE TABLE contracts (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID NOT NULL,

    supplier_id UUID,

    contract_number VARCHAR(100),

    start_date DATE,

    end_date DATE,

    contract_value NUMERIC(15,2),


    FOREIGN KEY(tenant_id)
        REFERENCES tenants(id),


    FOREIGN KEY(supplier_id)
        REFERENCES suppliers(id)

);



-- ==========================================================
-- PROCUREMENT
-- ==========================================================


CREATE TABLE purchase_requisitions (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID NOT NULL,

    requester_id UUID,

    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    FOREIGN KEY(tenant_id)
        REFERENCES tenants(id)

);



CREATE TABLE purchase_requisition_items (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    requisition_id UUID NOT NULL,

    description TEXT,

    quantity NUMERIC(15,2),

    unit_price NUMERIC(15,2),


    FOREIGN KEY(requisition_id)
        REFERENCES purchase_requisitions(id)

);



CREATE TABLE purchase_orders (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tenant_id UUID NOT NULL,

    supplier_id UUID,

    po_number VARCHAR(100),

    status VARCHAR(50),


    FOREIGN KEY(tenant_id)
        REFERENCES tenants(id),


    FOREIGN KEY(supplier_id)
        REFERENCES suppliers(id)

);



CREATE TABLE purchase_order_items (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    po_id UUID,

    description TEXT,

    quantity NUMERIC(15,2),

    price NUMERIC(15,2),


    FOREIGN KEY(po_id)
        REFERENCES purchase_orders(id)

);



-- ==========================================================
-- RECEIVING
-- ==========================================================


CREATE TABLE receipts (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    po_id UUID,

    received_date DATE,

    status VARCHAR(50),

    FOREIGN KEY(po_id)
        REFERENCES purchase_orders(id)

);



-- ==========================================================
-- INVOICE
-- ==========================================================


CREATE TABLE invoices (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    po_id UUID,

    invoice_number VARCHAR(100),

    amount NUMERIC(15,2),

    match_status VARCHAR(50),

    FOREIGN KEY(po_id)
        REFERENCES purchase_orders(id)

);



-- ==========================================================
-- WORKFLOW ENGINE
-- ==========================================================


CREATE TABLE workflow_instances (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    object_type VARCHAR(50),

    object_id UUID,

    status VARCHAR(50)

);



CREATE TABLE approval_tasks (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    workflow_id UUID,

    approver_id UUID,

    status VARCHAR(50),

    FOREIGN KEY(workflow_id)
        REFERENCES workflow_instances(id)

);



-- ==========================================================
-- AI INTELLIGENCE
-- ==========================================================


CREATE TABLE ai_recommendations (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    object_type VARCHAR(100),

    object_id UUID,

    recommendation JSONB,

    confidence NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);



-- END
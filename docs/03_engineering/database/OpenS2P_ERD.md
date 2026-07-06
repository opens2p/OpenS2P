# OpenS2P Database ERD

Version: 1.0  
Status: Draft  
Owner: OpenS2P Engineering  

---

# 1. Database Design Principles

OpenS2P database is designed for:

- Multi-tenant SaaS
- Source-to-Pay lifecycle
- Workflow driven approvals
- Audit compliance
- AI-ready procurement intelligence

Core rules:

- Every business table contains tenant_id
- Soft delete support
- Full audit trail
- API-first design
- Event driven integration

Standard columns:

```sql
id UUID PRIMARY KEY

tenant_id UUID

created_at TIMESTAMP
created_by UUID

updated_at TIMESTAMP
updated_by UUID

is_active BOOLEAN
```

---

# 2. Core Domains

OpenS2P data model contains:

1. Platform Administration
2. Supplier Management
3. Sourcing
4. Contract Management
5. Procurement
6. Receiving
7. Invoice Management
8. Workflow Engine
9. Integration Framework
10. AI Intelligence

---

# 3. Platform ERD


## tenants

Stores customer organizations.

Columns:

| Column | Type |
|-|-|
| id | UUID |
| name | varchar |
| tenant_code | varchar |
| status | varchar |


Relationships:

```
tenant
  |
  +--- users
  |
  +--- suppliers
  |
  +--- transactions
```


---

## users

Application users.

| Column | Type |
|-|-|
| id | UUID |
| tenant_id | UUID |
| email | varchar |
| first_name | varchar |
| last_name | varchar |
| status | varchar |


---

## roles

Security roles.

Examples:

- Admin
- Buyer
- Requester
- Approver
- Supplier


---

# 4. Supplier Management ERD


## suppliers

Supplier master.

| Column | Type |
|-|-|
| id | UUID |
| tenant_id | UUID |
| supplier_number | varchar |
| supplier_name | varchar |
| status | varchar |
| risk_score | decimal |


Relationships:

```
supplier

   |
   + supplier_contacts

   |
   + supplier_documents

   |
   + contracts

   |
   + purchase_orders
```


---

## supplier_contacts

| Column | Type |
|-|-|
| id UUID |
| supplier_id UUID |
| email varchar |
| phone varchar |


---

## supplier_documents

Stores certificates and attachments.


---

# 5. Sourcing ERD


## sourcing_events

RFQ/RFP events.

| Column | Type |
|-|-|
| id UUID |
| event_name varchar |
| event_type varchar |
| status varchar |


Relationship:

```
sourcing_event

      |
      +--- supplier_bids

      |
      +--- award
```

---

## supplier_bids

Supplier responses.


---

# 6. Contract ERD


## contracts


| Column | Type |
|-|-|
| id UUID |
| supplier_id UUID |
| contract_number varchar |
| start_date date |
| end_date date |
| value decimal |


---

# 7. Procurement ERD


## purchase_requisitions


PR header.


Relationship:

```
purchase_requisition

       |
       + purchase_requisition_items

       |
       + approval_workflow

       |
       + purchase_order
```


---

## purchase_orders


Relationship:

```
purchase_order

     |
     + purchase_order_items

     |
     + receipts

     |
     + invoices
```


---

# 8. Receiving ERD


## receipts


Tracks goods/service confirmation.


---

# 9. Invoice ERD


## invoices


Relationship:

```
invoice

 |
 + purchase_order

 |
 + matching_result
```


Supports:

- 2 way match
- 3 way match
- Exceptions


---

# 10. Workflow ERD


## workflow_instances


Tracks approval lifecycle.


## approval_tasks


Example:

PR Approval

```
Created
   |
Manager Approval
   |
Finance Approval
   |
Approved
```


---

# 11. Integration ERD


## integration_logs


Tracks:

- SAP
- Email
- APIs
- Supplier Network


---

# 12. AI Intelligence ERD


## ai_recommendations


Stores AI decisions:

Examples:

- Category prediction
- Supplier suggestion
- Contract risk


Columns:

| Column | Type |
|-|-|
| id UUID |
| object_type varchar |
| object_id UUID |
| recommendation jsonb |
| confidence decimal |


---

# 13. High Level Relationship Diagram


```text

Tenant
 |
 +-- Users
 |
 +-- Suppliers
        |
        +-- Contracts
        |
        +-- Sourcing Events
        |
        +-- Purchase Orders
                 |
                 +-- Receipts
                 |
                 +-- Invoices


Purchase Requisition
        |
        +-- Workflow
        |
        +-- Purchase Order


AI Layer
        |
        +-- Recommendations
        +-- Risk Analysis

```

---

# Next Engineering Outputs

- PostgreSQL schema
- SQLAlchemy Models
- Alembic Migration
- API Specification

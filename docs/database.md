# Database Design

## Database

MariaDB

## Naming Convention

Tables

- users
- organizations
- suppliers
- purchase_requisitions
- purchase_orders
- invoices

Primary Keys

- id (UUID)

Audit Columns

- created_at
- created_by
- updated_at
- updated_by
- deleted

## Initial Tables

Core

- organizations
- users
- roles
- permissions
- user_roles

Supplier

- suppliers
- supplier_contacts
- supplier_addresses
- supplier_categories

Procurement

- purchase_requisitions
- purchase_requisition_items
- purchase_orders
- purchase_order_items

Invoice

- invoices
- invoice_items

Contract

- contracts

Analytics

- spend_summary

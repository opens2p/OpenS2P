# REST API

## Base URL

```
/api/v1
```

## Authentication

JWT Bearer Token

## Endpoints

### Authentication

POST /auth/login

POST /auth/logout

POST /auth/refresh

---

### Users

GET /users

GET /users/{id}

POST /users

PUT /users/{id}

DELETE /users/{id}

---

### Suppliers

GET /suppliers

POST /suppliers

PUT /suppliers/{id}

DELETE /suppliers/{id}

---

### Purchase Requisitions

GET /purchase-requisitions

POST /purchase-requisitions

---

### Purchase Orders

GET /purchase-orders

POST /purchase-orders

---

### Invoices

GET /invoices

POST /invoices

---

## Response Format

```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

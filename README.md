<div align="center">
  <h1>OpenS2P</h1>
  <p><strong>Enterprise Open-Source Source-to-Pay Platform</strong></p>
  <p>
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-api-documentation">API Docs</a> •
    <a href="#-development">Development</a> •
    <a href="#-deployment">Deployment</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/version-0.7.0-blueviolet" alt="Version 0.7.0">
    <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12">
    <img src="https://img.shields.io/badge/react-19-purple" alt="React 19">
    <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License Apache 2.0">
  </p>
</div>

---

**OpenS2P v0.7 Enterprise MVP** is a modern, open-source Source-to-Pay (S2P) platform built for the enterprise. It covers the complete procurement lifecycle — from supplier onboarding through invoice payment — with AI-powered intelligence embedded at every step.

## OpenAI Build Week

OpenS2P was built with OpenAI GPT-5 and Codex.

GPT-5 was used to design and implement AI-assisted procurement features, while Codex accelerated development by assisting with architecture, FastAPI endpoints, SQLAlchemy models, database migrations, debugging, documentation, and testing.

## ✅ v0.7 Enterprise MVP — Feature Complete

| Domain | Status |
|---|---|
| **Supplier Management** — Onboard, approve, block, risk-score | ✅ |
| **Contract Management** — Lifecycle, renewals, compliance | ✅ |
| **Procurement** — Purchase Requisitions → Approvals → Purchase Orders | ✅ |
| **Invoice Matching** — 2-way/3-way matching with exception handling | ✅ |
| **Receiving** — Goods receipt against POs with quantity validation | ✅ |
| **Workflow Engine** — Configurable approval workflows | ✅ |
| **Analytics** — Spend analysis, supplier scorecards, dashboards | ✅ |
| **Integration Framework** — Pluggable connectors (REST, SFTP, etc.) | ✅ |
| **AI Intelligence** — Risk scoring, contract review, anomaly detection | ✅ |
| **Audit Trail** — Immutable change history with activity timeline | ✅ |
| **RBAC** — Role-based access control (7 roles, 29 permissions) | ✅ |
| **Multi-Tenant** — SaaS-ready tenant isolation | ✅ |

## Features

- **Supplier Management** — Onboard, approve, block, and risk-score suppliers
- **Sourcing** — RFQ/RFP events with supplier bidding and award
- **Contract Management** — Full contract lifecycle with AI clause review
- **Procurement** — Purchase Requisitions → Approvals → Purchase Orders
- **Receiving** — Goods receipt against POs with quantity validation
- **Invoice Matching** — 2-way and 3-way matching with exception handling
- **Workflow Engine** — Configurable approval workflows with delegation
- **AI Intelligence** — Risk scoring, contract review, anomaly detection
- **Audit Trail** — Immutable change history with activity timeline
- **Multi-Tenant** — SaaS-ready tenant isolation
- **RBAC** — Role-based access control with 7 roles and 29 permissions

## Quick Start

### Prerequisites

- Docker & Docker Compose

### Run the full stack

```bash
docker compose up --build
```

> **Note:** Database migrations run automatically on startup. Seed data is loaded separately — see below.

| Service | URL |
|---|---|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### Seed demo data

```bash
docker compose exec backend python -m app.db.seed
```

Or locally:

```bash
cd backend
python -m app.db.seed
```

### Demo credentials

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@12345` | System Admin |
| `buyer` | `Buyer@12345` | Buyer |
| `approver` | `Approver@12345` | Approver |
| `requester` | `Requester@12345` | Requester |
| `finance` | `Finance@12345` | Finance |

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                      Frontend                          │
│           React 19 · TypeScript · Tailwind              │
│           TanStack Query · React Router                 │
└──────────────────────┬─────────────────────────────────┘
                       │  HTTP / JSON
                       ▼
┌────────────────────────────────────────────────────────┐
│                     Backend API                        │
│      FastAPI · Python 3.12 · Pydantic V2               │
│                                                         │
│  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌────────────┐  │
│  │ Service  │ │Workflow │ │  Audit  │ │    AI      │  │
│  │  Layer   │ │ Engine  │ │  Trail  │ │Intelligence│  │
│  └────┬─────┘ └─────────┘ └─────────┘ └────────────┘  │
│       │                                                 │
│  ┌────▼─────┐                                           │
│  │Repository│                                           │
│  │  Layer   │                                           │
│  └────┬─────┘                                           │
└───────┼─────────────────────────────────────────────────┘
        │  asyncpg
        ▼
┌────────────────┐
│   PostgreSQL   │
│     16         │
└────────────────┘
```

### Layered Design

```
HTTP Request → FastAPI Endpoint → Service Layer → Repository Layer → SQLAlchemy → PostgreSQL
```

## API Documentation

With the server running, visit **http://localhost:8000/docs** (Swagger UI).

### Endpoints (43 total)

| Domain | Key Endpoints |
|---|---|
| **Auth** | `POST /auth/login`, `GET /auth/me` |
| **Suppliers** | `CRUD + POST /approve, /block` |
| **Contracts** | `CRUD + POST /activate, /renew` |
| **Sourcing** | `Events CRUD + bids + award` |
| **PR** | `CRUD + POST /approve, /reject` |
| **PO** | `CRUD + POST /send, /close` |
| **Invoices** | `CRUD + POST /match, /approve` |
| **Audit** | `GET /audit/{type}/{id}`, `/recent`, `/user/{id}` |
| **AI** | `GET /ai/supplier/{id}/analyze`, `/contract/{id}/review`, `/invoice/{id}/analyze` |

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # → http://localhost:5173
```

### Testing

```bash
cd backend
pytest ../tests/ -v
```

## Deployment

```bash
docker compose up --build -d
```

Configure via environment variables (see `.env.example`):

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Token signing key |
| `OPENAI_API_KEY` | Required for AI features |

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2 |
| **Database** | PostgreSQL 16, Alembic |
| **Frontend** | React 19, TypeScript, Tailwind, TanStack Query |
| **Auth** | JWT (HS256), bcrypt, RBAC |
| **AI** | Pluggable (local / OpenAI) |
| **Infrastructure** | Docker, Docker Compose |

## Project Structure

```
OpenS2P/
├── backend/
│   ├── app/
│   │   ├── ai/           # AI intelligence services
│   │   ├── api/v1/       # REST endpoints
│   │   ├── core/         # Config, exceptions
│   │   ├── db/           # Session, seed data
│   │   ├── models/       # SQLAlchemy ORM (27 tables)
│   │   ├── repositories/ # Data access layer
│   │   ├── schemas/      # Pydantic DTOs
│   │   ├── security/     # JWT, passwords, RBAC
│   │   └── services/     # Business logic
│   ├── alembic/          # Migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # API client & types
│   │   ├── components/   # Reusable UI
│   │   ├── pages/        # 12 route pages
│   │   └── layouts/      # Dashboard shell
│   └── Dockerfile
├── tests/                # Backend tests
├── docker-compose.yml
└── README.md
```

## Roadmap

- [x] Supplier lifecycle management
- [x] Sourcing events & bidding
- [x] Contract management
- [x] Purchase requisitions & approvals
- [x] Purchase orders
- [x] Goods receiving
- [x] Invoice matching
- [x] Audit trail & activity timeline
- [x] AI-powered risk analysis
- [x] Multi-tenant SaaS isolation
- [ ] OAuth 2.0 / SSO
- [ ] Supplier portal
- [ ] E-procurement catalog
- [ ] Advanced AI: LLM clause extraction
- [ ] Budget management
- [ ] Analytics dashboard

## Contributing

We welcome contributors — engineers, architects, security researchers, technical writers, and procurement domain experts. See [CONTRIBUTING.md](./CONTRIBUTING.md) to get started, and look for issues labeled [`good first issue`](https://github.com/opens2p/OpenS2P/labels/good%20first%20issue). Please also read our [Code of Conduct](./CODE_OF_CONDUCT.md).

## Sponsor

OpenS2P is free and open source. Sponsorship funds infrastructure, security audits, and the AI evaluation program: [github.com/sponsors/opens2p](https://github.com/sponsors/opens2p)

## License

Apache 2.0 — see [LICENSE](./LICENSE). Procura AI and ContractEdge are commercial applications built on the OpenS2P platform; the platform itself is fully open source.

## Contact

- Website: [opens2p.org](https://opens2p.org)
- Email: opens2p@gmail.com
- LinkedIn: [linkedin.com/company/opens2p](https://www.linkedin.com/company/opens2p)

---

<p align="center">Built for the open-source procurement community</p>

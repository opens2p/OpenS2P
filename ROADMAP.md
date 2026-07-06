# OpenS2P Roadmap

> **Current version:** 0.1.0 (MVP Release Candidate)
> **Status:** Community Edition — Pre-Launch

## ✅ Completed (v0.1.0)

### Core Platform
- [x] Multi-tenant architecture with tenant isolation
- [x] JWT authentication with bcrypt password hashing
- [x] RBAC — 7 roles, 29 permissions
- [x] Request-ID middleware for tracing
- [x] Pydantic v2 settings management
- [x] Database migrations via Alembic

### Supplier Management
- [x] Supplier lifecycle (Draft → Approved → Blocked)
- [x] Supplier risk scoring (AI-powered)
- [x] Supplier search and status filtering
- [x] Contacts and documents

### Sourcing
- [x] RFQ/RFP event creation
- [x] Supplier bidding
- [x] Bid evaluation and award

### Contract Management
- [x] Contract lifecycle (Create → Activate → Renew → Expire)
- [x] AI-powered contract clause review
- [x] Expiration alerts

### Procurement
- [x] Purchase Requisition with line items
- [x] PR approval workflow
- [x] Purchase Order with line items
- [x] PO lifecycle (Create → Send → Confirm → Close)
- [x] Goods receiving

### Invoicing
- [x] Invoice submission
- [x] 2-way / 3-way matching
- [x] Exception queue
- [x] Payment approval

### Workflow Engine
- [x] Configurable approval workflows
- [x] Approve / Reject / Delegate / Escalate
- [x] Pending task inbox

### AI Intelligence
- [x] Supplier risk analysis
- [x] Contract clause review
- [x] Invoice anomaly detection
- [x] AI Governance (execution audit trail)

### Audit & Compliance
- [x] Immutable audit event log
- [x] Activity timeline per entity
- [x] Global activity feed
- [x] User action history

### Frontend
- [x] React 19 + TypeScript + Tailwind
- [x] JWT login with token management
- [x] Dashboard with stats cards
- [x] Supplier module (list, detail, create, approve, block)
- [x] Contract module (list, detail)
- [x] Procurement module (PR list, create, approve; PO list, create, send, close)
- [x] Invoice module (list, match, approve)
- [x] Receiving page
- [x] Workflow inbox (approve/reject)
- [x] AI intelligence dashboard
- [x] Activity timeline component

### Infrastructure
- [x] Docker Compose (PostgreSQL + Backend + Frontend)
- [x] GitHub Actions CI/CD (4 workflows)
- [x] Backend testing with pytest-asyncio
- [x] Production configuration (.env)

---

## 🔜 Next (v0.2.0)

### Authentication
- [ ] OAuth 2.0 / SSO (Google, Microsoft, GitHub)
- [ ] Refresh tokens
- [ ] Session management
- [ ] MFA / TOTP support

### Supplier Portal
- [ ] Supplier self-registration
- [ ] Supplier document upload
- [ ] Bid submission interface
- [ ] Invoice submission via portal

### E-Procurement
- [ ] Product catalog with categories
- [ ] Punch-out / marketplace integration
- [ ] Shopping cart experience
- [ ] Guided buying

### Advanced AI
- [ ] LLM-based contract clause extraction
- [ ] Supplier 360° score (financial + ESG + performance)
- [ ] Fraud detection on invoice patterns
- [ ] AI-powered negotiation assistant
- [ ] Spend classification and analytics

### Platform
- [ ] Analytics dashboard with charts
- [ ] Budget management and tracking
- [ ] Email notifications (SendGrid / SES)
- [ ] Webhook event system
- [ ] API rate limiting

### Deployment
- [ ] Helm chart for Kubernetes
- [ ] Terraform module for cloud provisioning
- [ ] Managed PostgreSQL support (RDS, Cloud SQL)
- [ ] Redis caching layer

---

## 🗺️ Future (v0.3.0+)

- **Multi-language / i18n** — Internationalization for global teams
- **Mobile app** — React Native for approval on the go
- **Fieldglass/VMS** — Vendor management system for contingent workforce
- **ESG tracking** — Supplier sustainability scoring
- **Procurement analytics** — ML-driven spend insights
- **Blockchain** — Immutable audit for regulated industries

---

*Roadmap is subject to change based on community feedback and priorities.*

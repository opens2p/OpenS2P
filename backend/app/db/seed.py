"""
OpenS2P – Seed Data Loader
===========================
Idempotent seed script that bootstraps the platform with:

* Default tenant
* Admin user and RBAC roles
* Procurement master data (currencies, countries, categories, UOM)
* Workflow approval templates
* Demonstration supplier / contract / PR / PO / invoice

Usage:
    python -m app.db.seed

Or from application startup:
    from app.db.seed import seed_database
    await seed_database()
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

# Use the application bcrypt-based password hasher
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.security.password import hash_password

# ---------------------------------------------------------------------------
# deterministic UUID generation (idempotent: same name → same UUID)
# ---------------------------------------------------------------------------

_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


def _uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, f"opens2p:{name}")


# ---------------------------------------------------------------------------
# master data helpers
# ---------------------------------------------------------------------------

SEED_TENANT_ID = _uuid("tenant:demo")
SEED_ADMIN_USER_ID = _uuid("user:admin")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# pylint: disable=too-many-locals,too-many-statements
def seed_database(engine: Engine) -> None:
    """Idempotent seed — safe to run multiple times."""
    with Session(engine) as session:

        # ── 1. TENANT ────────────────────────────────────────────────────
        _upsert(
            session,
            "tenants",
            dict(
                id=SEED_TENANT_ID,
                tenant_code="DEMO",
                name="OpenS2P Demo Corporation",
                status="ACTIVE",
                created_at=_now(),
                updated_at=_now(),
                is_active=True,
            ),
            conflict_col="tenant_code",
        )
        session.flush()

        # ── 2. USERS (before roles — FKs require users to exist) ────────
        users: list[dict[str, Any]] = [
            dict(
                id=SEED_ADMIN_USER_ID,
                username="admin",
                email="admin@opens2p.com",
                first_name="System",
                last_name="Admin",
                hashed_password=hash_password("Admin@12345"),
                is_superuser=True,
            ),
            dict(
                id=_uuid("user:buyer"),
                username="buyer",
                email="buyer@opens2p.com",
                first_name="Sarah",
                last_name="Chen",
                hashed_password=hash_password("Buyer@12345"),
                is_superuser=False,
            ),
            dict(
                id=_uuid("user:approver"),
                username="approver",
                email="approver@opens2p.com",
                first_name="James",
                last_name="Wilson",
                hashed_password=hash_password("Approver@12345"),
                is_superuser=False,
            ),
            dict(
                id=_uuid("user:requester"),
                username="requester",
                email="requester@opens2p.com",
                first_name="Lisa",
                last_name="Park",
                hashed_password=hash_password("Requester@12345"),
                is_superuser=False,
            ),
            dict(
                id=_uuid("user:finance"),
                username="finance",
                email="finance@opens2p.com",
                first_name="Robert",
                last_name="Martinez",
                hashed_password=hash_password("Finance@12345"),
                is_superuser=False,
            ),
        ]

        for u in users:
            uid = u["id"]
            # First user (admin) has created_by=None to break the circular FK
            cb = SEED_ADMIN_USER_ID if uid != SEED_ADMIN_USER_ID else None
            _upsert(
                session,
                "users",
                dict(
                    id=uid,
                    tenant_id=SEED_TENANT_ID,
                    username=u["username"],
                    email=u["email"],
                    first_name=u["first_name"],
                    last_name=u["last_name"],
                    hashed_password=u["hashed_password"],
                    is_superuser=u["is_superuser"],
                    created_at=_now(),
                    updated_at=_now(),
                    created_by=cb,
                    updated_by=cb,
                    is_active=True,
                ),
                conflict_col="username",
            )
        session.flush()

        # ── 3. ROLES ─────────────────────────────────────────────────────
        roles: dict[str, dict[str, Any]] = {
            "SYSTEM_ADMIN": dict(
                description="Platform-wide super-admin — all permissions",
            ),
            "PROCUREMENT_ADMIN": dict(
                description="Manages procurement configuration and master data",
            ),
            "BUYER": dict(
                description="Creates purchase orders and manages supplier relationships",
            ),
            "REQUESTER": dict(
                description="Submits purchase requisitions for approval",
            ),
            "APPROVER": dict(
                description="Reviews and approves requisitions, POs, and invoices",
            ),
            "SUPPLIER_USER": dict(
                description="Supplier portal user — submits bids and invoices",
            ),
            "FINANCE_USER": dict(
                description="Invoice processing, payment reconciliation",
            ),
        }

        role_ids: dict[str, uuid.UUID] = {}
        for role_name, meta in roles.items():
            rid = _uuid(f"role:{role_name}")
            role_ids[role_name] = rid
            _upsert(
                session,
                "roles",
                dict(
                    id=rid,
                    tenant_id=SEED_TENANT_ID,
                    role_name=role_name,
                    description=meta["description"],
                    created_at=_now(),
                    updated_at=_now(),
                    created_by=SEED_ADMIN_USER_ID,
                    updated_by=SEED_ADMIN_USER_ID,
                    is_active=True,
                ),
                conflict_col="id",
            )
        session.flush()

        # ── assign users to roles ────────────────────────────────────────
        user_role_assignments: list[tuple[str, str]] = [
            ("admin", "SYSTEM_ADMIN"),
            ("admin", "PROCUREMENT_ADMIN"),
            ("buyer", "BUYER"),
            ("approver", "APPROVER"),
            ("requester", "REQUESTER"),
            ("finance", "FINANCE_USER"),
        ]
        for uname, rname in user_role_assignments:
            _upsert(
                session,
                "user_roles",
                dict(
                    id=_uuid(f"user_role:{uname}:{rname}"),
                    user_id=_uuid(f"user:{uname}"),
                    role_id=role_ids[rname],
                    tenant_id=SEED_TENANT_ID,
                    created_at=_now(),
                    updated_at=_now(),
                    created_by=SEED_ADMIN_USER_ID,
                    updated_by=SEED_ADMIN_USER_ID,
                    is_active=True,
                ),
                conflict_col="id",
            )
        session.flush()

        # ── 4. MASTER DATA ───────────────────────────────────────────────
        _seed_currencies(session)
        _seed_countries(session)
        _seed_categories(session)
        _seed_uom(session)
        session.flush()

        # ── 5. WORKFLOW TEMPLATES ────────────────────────────────────────
        _seed_workflow_templates(session)
        session.flush()

        # ── 6. DEMO DATA ─────────────────────────────────────────────────
        _seed_demo_data(session)
        session.flush()

        session.commit()
        print("✅ Seed data loaded successfully.")


# ═══════════════════════════════════════════════════════════════════════════
# Master data seeders
# ═══════════════════════════════════════════════════════════════════════════

_CURRENCIES = [
    ("USD", "US Dollar", "$"),
    ("EUR", "Euro", "€"),
    ("GBP", "British Pound", "£"),
    ("JPY", "Japanese Yen", "¥"),
    ("INR", "Indian Rupee", "₹"),
    ("CAD", "Canadian Dollar", "C$"),
    ("AUD", "Australian Dollar", "A$"),
    ("CHF", "Swiss Franc", "Fr"),
    ("CNY", "Chinese Yuan", "¥"),
    ("SGD", "Singapore Dollar", "S$"),
]

_COUNTRIES = [
    ("US", "United States", "USD"),
    ("GB", "United Kingdom", "GBP"),
    ("DE", "Germany", "EUR"),
    ("FR", "France", "EUR"),
    ("JP", "Japan", "JPY"),
    ("IN", "India", "INR"),
    ("CA", "Canada", "CAD"),
    ("AU", "Australia", "AUD"),
    ("CH", "Switzerland", "CHF"),
    ("SG", "Singapore", "SGD"),
    ("CN", "China", "CNY"),
    ("NL", "Netherlands", "EUR"),
    ("SE", "Sweden", "EUR"),
    ("KR", "South Korea", "USD"),
]

_CATEGORIES = [
    ("IT_HARDWARE", "IT Hardware", "Computers, servers, networking equipment"),
    ("SOFTWARE", "Software", "Licenses, SaaS subscriptions, cloud services"),
    ("OFFICE_SUPPLIES", "Office Supplies", "Stationery, furniture, consumables"),
    ("CONSULTING", "Consulting", "Management, technical, legal consulting services"),
    ("MARKETING", "Marketing", "Advertising, branding, promotional materials"),
    ("TRAVEL", "Travel", "Flights, hotels, ground transportation"),
    ("FACILITIES", "Facilities", "Maintenance, cleaning, utilities"),
    ("RAW_MATERIALS", "Raw Materials", "Production inputs, components, packaging"),
    ("LOGISTICS", "Logistics", "Shipping, warehousing, freight services"),
    ("PROFESSIONAL_SERVICES", "Professional Services", "Audit, legal, insurance"),
]

_UOM = [
    ("EA", "Each", "Individual unit count"),
    ("KG", "Kilogram", "Metric weight unit"),
    ("LB", "Pound", "Imperial weight unit"),
    ("HR", "Hour", "Time-based service"),
    ("DAY", "Day", "Daily rate or rental"),
    ("MO", "Month", "Monthly subscription or lease"),
    ("YR", "Year", "Annual subscription"),
    ("M2", "Square Meter", "Area measurement"),
    ("L", "Liter", "Volume measurement"),
    ("BOX", "Box", "Box / case quantity"),
    ("SET", "Set", "Set / kit of items"),
    ("SVC", "Service", "Professional service deliverable"),
]


def _seed_currencies(session: Session) -> None:
    for code, name, symbol in _CURRENCIES:
        _upsert(
            session,
            "currencies",
            dict(
                id=_uuid(f"currency:{code}"),
                tenant_id=SEED_TENANT_ID,
                currency_code=code,
                currency_name=name,
                symbol=symbol,
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
                created_by=SEED_ADMIN_USER_ID,
                updated_by=SEED_ADMIN_USER_ID,
            ),
            conflict_col="id",
        )
    print(f"  ✓ {len(_CURRENCIES)} currencies seeded")


def _seed_countries(session: Session) -> None:
    for code, name, currency_code in _COUNTRIES:
        _upsert(
            session,
            "countries",
            dict(
                id=_uuid(f"country:{code}"),
                tenant_id=SEED_TENANT_ID,
                country_code=code,
                country_name=name,
                currency_code=currency_code,
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
                created_by=SEED_ADMIN_USER_ID,
                updated_by=SEED_ADMIN_USER_ID,
            ),
            conflict_col="id",
        )
    print(f"  ✓ {len(_COUNTRIES)} countries seeded")


def _seed_categories(session: Session) -> None:
    for code, name, desc in _CATEGORIES:
        _upsert(
            session,
            "categories",
            dict(
                id=_uuid(f"category:{code}"),
                tenant_id=SEED_TENANT_ID,
                category_code=code,
                category_name=name,
                description=desc,
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
                created_by=SEED_ADMIN_USER_ID,
                updated_by=SEED_ADMIN_USER_ID,
            ),
            conflict_col="id",
        )
    print(f"  ✓ {len(_CATEGORIES)} categories seeded")


def _seed_uom(session: Session) -> None:
    for code, name, desc in _UOM:
        _upsert(
            session,
            "units_of_measure",
            dict(
                id=_uuid(f"uom:{code}"),
                tenant_id=SEED_TENANT_ID,
                uom_code=code,
                uom_name=name,
                description=desc,
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
                created_by=SEED_ADMIN_USER_ID,
                updated_by=SEED_ADMIN_USER_ID,
            ),
            conflict_col="id",
        )
    print(f"  ✓ {len(_UOM)} units of measure seeded")


# ═══════════════════════════════════════════════════════════════════════════
# Workflow templates
# ═══════════════════════════════════════════════════════════════════════════

_WORKFLOW_TEMPLATES: list[dict[str, Any]] = [
    dict(
        name="PR_APPROVAL",
        label="PR Approval",
        description="Purchase Requisition approval chain",
        steps=[
            "DRAFT",
            "MANAGER_APPROVAL",
            "FINANCE_APPROVAL",
            "APPROVED",
        ],
    ),
    dict(
        name="PO_APPROVAL",
        label="PO Approval",
        description="Purchase Order approval with budget check",
        steps=[
            "DRAFT",
            "BUDGET_CHECK",
            "PROCUREMENT_MANAGER",
            "APPROVED",
        ],
    ),
    dict(
        name="SUPPLIER_ONBOARDING",
        label="Supplier Onboarding",
        description="New supplier registration and risk assessment",
        steps=[
            "DRAFT",
            "REVIEW",
            "RISK_CHECK",
            "APPROVED",
        ],
    ),
    dict(
        name="INVOICE_MATCH",
        label="Invoice Matching",
        description="Invoice validation and 3-way matching",
        steps=[
            "RECEIVED",
            "TWO_WAY_MATCH",
            "THREE_WAY_MATCH",
            "PAYMENT_READY",
        ],
    ),
]


def _seed_workflow_templates(session: Session) -> None:
    for tmpl in _WORKFLOW_TEMPLATES:
        _upsert(
            session,
            "workflow_templates",
            dict(
                id=_uuid(f"wf_template:{tmpl['name']}"),
                tenant_id=SEED_TENANT_ID,
                template_name=tmpl["name"],
                label=tmpl["label"],
                description=tmpl["description"],
                steps=json.dumps(tmpl["steps"]),
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
                created_by=SEED_ADMIN_USER_ID,
                updated_by=SEED_ADMIN_USER_ID,
            ),
            conflict_col="id",
        )
    print(f"  ✓ {len(_WORKFLOW_TEMPLATES)} workflow templates seeded")


# ═══════════════════════════════════════════════════════════════════════════
# Demo transactional data
# ═══════════════════════════════════════════════════════════════════════════

_DEMO_SUPPLIER_ID = _uuid("supplier:acme")
_DEMO_SUPPLIER2_ID = _uuid("supplier:globaltech")
_DEMO_SUPPLIER3_ID = _uuid("supplier:officeworks")
_DEMO_SUPPLIER4_ID = _uuid("supplier:horizon")
_DEMO_SUPPLIER5_ID = _uuid("supplier:precision")
_DEMO_SUPPLIER6_ID = _uuid("supplier:shield")
_DEMO_SUPPLIER7_ID = _uuid("supplier:transglobal")
_DEMO_SUPPLIER8_ID = _uuid("supplier:creative")
_DEMO_SUPPLIER9_ID = _uuid("supplier:cloudsaas")
_DEMO_SUPPLIER10_ID = _uuid("supplier:pinnacle")
_DEMO_CONTRACT_ID = _uuid("contract:acme-2026")
_DEMO_PR_ID = _uuid("pr:2026-001")
_DEMO_PO_ID = _uuid("po:2026-001")
_DEMO_PO2_ID = _uuid("po:2026-002")
_DEMO_PO3_ID = _uuid("po:2026-003")
_DEMO_PO4_ID = _uuid("po:2026-004")
_DEMO_PO5_ID = _uuid("po:2026-005")
_DEMO_INVOICE_ID = _uuid("invoice:inv-2026-001")
_DEMO_INVOICE2_ID = _uuid("invoice:inv-2026-002")
_DEMO_INVOICE3_ID = _uuid("invoice:inv-2026-003")
_DEMO_INVOICE4_ID = _uuid("invoice:inv-2026-004")
_DEMO_INVOICE5_ID = _uuid("invoice:inv-2026-005")
# 3-way match demo scenarios
_MATCH_PO_CLEAN = _uuid("po:match-clean")
_MATCH_PO_AUTO = _uuid("po:match-auto")
_MATCH_PO_NOGRN = _uuid("po:match-nogrn")
_MATCH_PO_ESC = _uuid("po:match-esc")
_MATCH_INV_CLEAN = _uuid("invoice:match-clean")
_MATCH_INV_AUTO = _uuid("invoice:match-auto")
_MATCH_INV_NOGRN = _uuid("invoice:match-nogrn")
_MATCH_INV_ESC = _uuid("invoice:match-esc")
_MATCH_GR_CLEAN = _uuid("receipt:match-clean")
_MATCH_GR_AUTO = _uuid("receipt:match-auto")
_MATCH_GR_ESC = _uuid("receipt:match-esc")


def _seed_demo_data(session: Session) -> None:
    buyer_id = _uuid("user:buyer")
    approver_id = _uuid("user:approver")
    finance_id = _uuid("user:finance")

    # ── Suppliers ────────────────────────────────────────────────────────
    suppliers_data = [
        dict(
            id=_DEMO_SUPPLIER_ID,
            supplier_number="SUP-00001",
            supplier_name="Microsoft Corporation",
            status="APPROVED",
            risk_score=5.00,
            description="Enterprise software, cloud services, and hardware solutions",
            address="1 Microsoft Way, Redmond, WA 98052, United States",
            extras=json.dumps({
                "payment_terms": "NET30",
                "delivery_lead_days": 10,
                "certifications": ["ISO_9001", "ISO_27001", "SOC2"],
                "category": "Software",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER2_ID,
            supplier_number="SUP-00002",
            supplier_name="Dell Technologies",
            status="APPROVED",
            risk_score=8.00,
            description="Enterprise IT hardware, servers, workstations, and data center infrastructure",
            address="1 Dell Way, Round Rock, TX 78682, United States",
            extras=json.dumps({
                "payment_terms": "NET45",
                "delivery_lead_days": 5,
                "certifications": ["ISO_9001", "ISO_27001", "SOC2"],
                "category": "IT Hardware",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER3_ID,
            supplier_number="SUP-00003",
            supplier_name="Amazon Web Services",
            status="APPROVED",
            risk_score=4.00,
            description="Cloud infrastructure, computing, storage, and enterprise cloud services",
            address="410 Terry Avenue North, Seattle, WA 98109, United States",
            extras=json.dumps({
                "payment_terms": "NET30",
                "delivery_lead_days": 0,
                "certifications": ["ISO_9001", "ISO_27001", "SOC2", "HIPAA"],
                "category": "Software",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER4_ID,
            supplier_number="SUP-00004",
            supplier_name="Accenture PLC",
            status="APPROVED",
            risk_score=10.00,
            description="Management consulting, technology services, and digital transformation",
            address="161 N Clark Street, Chicago, IL 60601, United States",
            extras=json.dumps({
                "payment_terms": "NET60",
                "delivery_lead_days": 0,
                "certifications": ["ISO_9001", "ISO_27001"],
                "category": "Professional Services",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER5_ID,
            supplier_number="SUP-00005",
            supplier_name="Infosys Limited",
            status="APPROVED",
            risk_score=12.00,
            description="IT consulting, outsourcing, and digital services",
            address="44 Electronics City, Hosur Road, Bangalore 560100, India",
            extras=json.dumps({
                "payment_terms": "NET45",
                "delivery_lead_days": 0,
                "certifications": ["ISO_9001", "ISO_27001", "CMMI_5"],
                "category": "Professional Services",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER6_ID,
            supplier_number="SUP-00006",
            supplier_name="Siemens AG",
            status="APPROVED",
            risk_score=6.00,
            description="Industrial automation, manufacturing equipment, and facility solutions",
            address="Werner-von-Siemens-Strasse 1, Munich 80333, Germany",
            extras=json.dumps({
                "payment_terms": "NET30",
                "delivery_lead_days": 15,
                "certifications": ["ISO_9001", "ISO_14001", "ISO_45001"],
                "category": "Facilities",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER7_ID,
            supplier_number="SUP-00007",
            supplier_name="DHL Supply Chain",
            status="APPROVED",
            risk_score=7.00,
            description="International logistics, warehousing, and supply chain management",
            address="Deutsche Post Platz 1, Bonn 53113, Germany",
            extras=json.dumps({
                "payment_terms": "NET45",
                "delivery_lead_days": 0,
                "certifications": ["ISO_9001", "ISO_14001", "AEO", "GDP"],
                "category": "Logistics",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER8_ID,
            supplier_number="SUP-00008",
            supplier_name="WPP Group",
            status="APPROVED",
            risk_score=9.00,
            description="Global advertising, marketing, and communications services",
            address="Sea Containers, 18 Upper Ground, London SE1 9GL, United Kingdom",
            extras=json.dumps({
                "payment_terms": "NET30",
                "delivery_lead_days": 5,
                "certifications": ["ISO_9001", "ISO_14001"],
                "category": "Marketing",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER9_ID,
            supplier_number="SUP-00009",
            supplier_name="Salesforce Inc.",
            status="DRAFT",
            risk_score=5.00,
            description="CRM platform, enterprise cloud applications, and AI solutions",
            address="415 Mission Street, San Francisco, CA 94105, United States",
            extras=json.dumps({
                "payment_terms": "NET30",
                "delivery_lead_days": 0,
                "certifications": ["ISO_27001", "SOC2", "HIPAA"],
                "category": "Software",
            }),
        ),
        dict(
            id=_DEMO_SUPPLIER10_ID,
            supplier_number="SUP-00010",
            supplier_name="McKinsey & Company",
            status="REGISTERED",
            risk_score=15.00,
            description="Strategic management consulting and advisory services",
            address="55 East 52nd Street, New York, NY 10055, United States",
            extras=json.dumps({
                "payment_terms": "NET60",
                "delivery_lead_days": 0,
                "certifications": ["ISO_9001"],
                "category": "Professional Services",
            }),
        ),
    ]

    for sup in suppliers_data:
        _upsert(
            session,
            "suppliers",
            dict(
                id=sup["id"],
                tenant_id=SEED_TENANT_ID,
                supplier_number=sup["supplier_number"],
                supplier_name=sup["supplier_name"],
                status=sup["status"],
                risk_score=sup["risk_score"],
                description=sup["description"],
                address=sup["address"],
                extras=sup["extras"],
                created_at=_now(),
                updated_at=_now(),
                created_by=buyer_id,
                updated_by=buyer_id,
                is_active=True,
            ),
            conflict_col="supplier_number",
        )

    # ── Contract ─────────────────────────────────────────────────────────
    _upsert(
        session,
        "contracts",
        dict(
            id=_DEMO_CONTRACT_ID,
            tenant_id=SEED_TENANT_ID,
            contract_number="CNTR-2026-001",
            supplier_id=_DEMO_SUPPLIER_ID,
            contract_value=250_000.00,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            description="Annual MRO supply agreement with volume pricing",
            created_at=_now(),
            updated_at=_now(),
            created_by=buyer_id,
            updated_by=buyer_id,
            is_active=True,
        ),
        conflict_col="id",
    )

    # ── Purchase Requisitions ────────────────────────────────────────────
    pr_defs = [
        dict(
            id=_DEMO_PR_ID,
            pr_number="PR-260710-00001",
            status="APPROVED",
            requester_id=_uuid("user:requester"),
            supplier_id=_DEMO_SUPPLIER_ID,
            description="Q2 MRO supply order — safety equipment and tools",
            items=[
                dict(id=_uuid("pr_item:safety-helmets"), description="Safety helmets (ANSI Z89.1 certified)", quantity=50, unit_price=34.50),
                dict(id=_uuid("pr_item:safety-goggles"), description="Industrial safety goggles, anti-fog", quantity=100, unit_price=12.75),
            ],
        ),
        dict(
            id=_uuid("pr:2026-002"),
            pr_number="PR-260710-00002",
            status="SUBMITTED",
            requester_id=_uuid("user:requester"),
            supplier_id=_DEMO_SUPPLIER2_ID,
            description="Server infrastructure upgrade — Q3 data center refresh",
            items=[
                dict(id=_uuid("pr_item:servers"), description="Dell PowerEdge R760xs servers", quantity=4, unit_price=12500.00),
                dict(id=_uuid("pr_item:ssd"), description="Enterprise SSD 3.84TB", quantity=16, unit_price=850.00),
            ],
        ),
        dict(
            id=_uuid("pr:2026-003"),
            pr_number="PR-260710-00003",
            status="DRAFT",
            requester_id=_uuid("user:requester"),
            supplier_id=None,
            description="Office furniture and ergonomic equipment for new hires",
            items=[
                dict(id=_uuid("pr_item:desks"), description="Standing desks 60x30", quantity=10, unit_price=899.00),
                dict(id=_uuid("pr_item:chairs"), description="Ergonomic office chairs", quantity=10, unit_price=450.00),
            ],
        ),
    ]

    for prd in pr_defs:
        _upsert(
            session,
            "purchase_requisitions",
            dict(
                id=prd["id"],
                tenant_id=SEED_TENANT_ID,
                pr_number=prd["pr_number"],
                status=prd["status"],
                requester_id=prd["requester_id"],
                supplier_id=prd["supplier_id"],
                description=prd["description"],
                created_at=_now(),
                updated_at=_now(),
                created_by=prd["requester_id"],
                updated_by=approver_id,
                is_active=True,
            ),
            conflict_col="pr_number",
        )

        for item in prd["items"]:
            _upsert(
                session,
                "purchase_requisition_items",
                dict(
                    id=item["id"],
                    tenant_id=SEED_TENANT_ID,
                    requisition_id=prd["id"],
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    created_at=_now(),
                    updated_at=_now(),
                    created_by=prd["requester_id"],
                    updated_by=prd["requester_id"],
                    is_active=True,
                ),
                conflict_col="id",
            )

    # ── Purchase Order ───────────────────────────────────────────────────
    _upsert(
        session,
        "purchase_orders",
        dict(
            id=_DEMO_PO_ID,
            tenant_id=SEED_TENANT_ID,
            po_number="PO-260710-01001",
            supplier_id=_DEMO_SUPPLIER_ID,
            status="RECEIVED",
            created_at=_now(),
            updated_at=_now(),
            created_by=buyer_id,
            updated_by=buyer_id,
            is_active=True,
        ),
        conflict_col="po_number",
    )

    # PO items
    po_items = [
        dict(
            id=_uuid("po_item:safety-helmets"),
            po_id=_DEMO_PO_ID,
            description="Safety helmets (ANSI Z89.1 certified)",
            quantity=50,
            price=34.50,
        ),
        dict(
            id=_uuid("po_item:safety-goggles"),
            po_id=_DEMO_PO_ID,
            description="Industrial safety goggles, anti-fog",
            quantity=100,
            price=12.75,
        ),
    ]
    for item in po_items:
        _upsert(
            session,
            "purchase_order_items",
            dict(
                id=item["id"],
                tenant_id=SEED_TENANT_ID,
                po_id=item["po_id"],
                description=item["description"],
                quantity=item["quantity"],
                price=item["price"],
                created_at=_now(),
                updated_at=_now(),
                created_by=buyer_id,
                updated_by=buyer_id,
                is_active=True,
            ),
            conflict_col="id",
        )

    # ── Receipt ──────────────────────────────────────────────────────────
    _upsert(
        session,
        "receipts",
        dict(
            id=_uuid("receipt:po-2026-001"),
            tenant_id=SEED_TENANT_ID,
            receipt_number="GR-260710-00001",
            po_id=_DEMO_PO_ID,
            status="completed",
            received_date=date(2026, 3, 20),
            quantity_received=150,
            amount_received=3000.00,
            created_at=_now(),
            updated_at=_now(),
            created_by=buyer_id,
            updated_by=buyer_id,
            is_active=True,
        ),
        conflict_col="receipt_number",
    )

    # ── Additional POs ───────────────────────────────────────────────────
    po_defs = [
        dict(
            id=_DEMO_PO2_ID,
            po_number="PO-260710-01002",
            supplier_id=_DEMO_SUPPLIER2_ID,
            status="ACKNOWLEDGED",
        ),
        dict(
            id=_DEMO_PO3_ID,
            po_number="PO-260710-01003",
            supplier_id=_DEMO_SUPPLIER4_ID,
            status="SENT",
        ),
        dict(
            id=_DEMO_PO4_ID,
            po_number="PO-260710-01004",
            supplier_id=_DEMO_SUPPLIER6_ID,
            status="PARTIALLY_RECEIVED",
        ),
        dict(
            id=_DEMO_PO5_ID,
            po_number="PO-260710-01005",
            supplier_id=_DEMO_SUPPLIER9_ID,
            status="APPROVED",
        ),
    ]

    for pod in po_defs:
        _upsert(
            session,
            "purchase_orders",
            dict(
                id=pod["id"],
                tenant_id=SEED_TENANT_ID,
                po_number=pod["po_number"],
                supplier_id=pod["supplier_id"],
                status=pod["status"],
                created_at=_now(),
                updated_at=_now(),
                created_by=buyer_id,
                updated_by=buyer_id,
                is_active=True,
            ),
            conflict_col="po_number",
        )

    # PO items for additional POs
    _upsert(
        session,
        "purchase_order_items",
        dict(
            id=_uuid("po_item:servers"),
            tenant_id=SEED_TENANT_ID,
            po_id=_DEMO_PO2_ID,
            description="Dell PowerEdge R760xs servers",
            quantity=10,
            price=12500.00,
        ),
        conflict_col="id",
    )
    _upsert(
        session,
        "purchase_order_items",
        dict(
            id=_uuid("po_item:consulting"),
            tenant_id=SEED_TENANT_ID,
            po_id=_DEMO_PO3_ID,
            description="Digital transformation consulting engagement",
            quantity=1,
            price=82000.00,
        ),
        conflict_col="id",
    )
    _upsert(
        session,
        "purchase_order_items",
        dict(
            id=_uuid("po_item:security"),
            tenant_id=SEED_TENANT_ID,
            po_id=_DEMO_PO4_ID,
            description="Facility security equipment and installation",
            quantity=1,
            price=30000.00,
        ),
        conflict_col="id",
    )
    _upsert(
        session,
        "purchase_order_items",
        dict(
            id=_uuid("po_item:saas"),
            tenant_id=SEED_TENANT_ID,
            po_id=_DEMO_PO5_ID,
            description="Enterprise SaaS subscription — annual license",
            quantity=1,
            price=55000.00,
        ),
        conflict_col="id",
    )

    # ── Additional Invoices ──────────────────────────────────────────────
    invoice_defs = [
        dict(
            id=_DEMO_INVOICE_ID,
            invoice_number="INV-260315-00001",
            po_id=_DEMO_PO_ID,
            amount=2975.00,
            match_status="MATCHED",
            invoice_date=date(2026, 1, 15),
            due_date=date(2026, 2, 14),
            supplier_ref="ACM-INV-2026-001",
        ),
        dict(
            id=_DEMO_INVOICE2_ID,
            invoice_number="INV-260228-00002",
            po_id=_DEMO_PO2_ID,
            amount=125000.00,
            match_status="MATCHED",
            invoice_date=date(2026, 2, 28),
            due_date=date(2026, 3, 30),
            supplier_ref="GT-INV-2026-002",
        ),
        dict(
            id=_DEMO_INVOICE3_ID,
            invoice_number="INV-260331-00003",
            po_id=_DEMO_PO3_ID,
            amount=82000.00,
            match_status="MATCHED",
            invoice_date=date(2026, 3, 31),
            due_date=date(2026, 5, 30),
            supplier_ref="HC-INV-2026-003",
        ),
        dict(
            id=_DEMO_INVOICE4_ID,
            invoice_number="INV-260430-00004",
            po_id=_DEMO_PO4_ID,
            amount=30000.00,
            match_status="PENDING",
            invoice_date=date(2026, 4, 30),
            due_date=date(2026, 5, 30),
            supplier_ref="SS-INV-2026-004",
        ),
        dict(
            id=_DEMO_INVOICE5_ID,
            invoice_number="INV-260531-00005",
            po_id=_DEMO_PO5_ID,
            amount=55000.00,
            match_status="PENDING",
            invoice_date=date(2026, 5, 31),
            due_date=date(2026, 6, 30),
            supplier_ref="CST-INV-2026-005",
        ),
    ]

    for invd in invoice_defs:
        _upsert(
            session,
            "invoices",
            dict(
                id=invd["id"],
                tenant_id=SEED_TENANT_ID,
                invoice_number=invd["invoice_number"],
                po_id=invd["po_id"],
                amount=invd["amount"],
                match_status=invd["match_status"],
                invoice_date=invd["invoice_date"],
                due_date=invd["due_date"],
                extras=json.dumps({
                    "supplier_reference": invd["supplier_ref"],
                    "payment_terms": "NET30",
                }),
                created_at=_now(),
                updated_at=_now(),
                created_by=finance_id,
                updated_by=finance_id,
                is_active=True,
            ),
            conflict_col="invoice_number",
        )

    # ── Intelligent 3-Way Match demo scenarios ───────────────────────────
    # PO totals are always 10 × $100 = $1,000 for easy variance math.
    match_scenarios = [
        dict(
            po_id=_MATCH_PO_CLEAN,
            po_number="PO-MATCH-CLEAN",
            inv_id=_MATCH_INV_CLEAN,
            inv_number="INV-MATCH-CLEAN",
            amount=1000.00,
            match_status="PENDING",
            gr_id=_MATCH_GR_CLEAN,
            gr_number="GR-MATCH-CLEAN",
            has_grn=True,
            scenario="clean",
        ),
        dict(
            po_id=_MATCH_PO_AUTO,
            po_number="PO-MATCH-AUTO",
            inv_id=_MATCH_INV_AUTO,
            inv_number="INV-MATCH-AUTO",
            amount=1060.00,  # +6% → EXCEPTION on match ($60 > $50), Auto-Resolve within $100
            match_status="PENDING",
            gr_id=_MATCH_GR_AUTO,
            gr_number="GR-MATCH-AUTO",
            has_grn=True,
            scenario="auto_variance",
        ),
        dict(
            po_id=_MATCH_PO_NOGRN,
            po_number="PO-MATCH-NOGRN",
            inv_id=_MATCH_INV_NOGRN,
            inv_number="INV-MATCH-NOGRN",
            amount=1000.00,
            match_status="PENDING",
            gr_id=None,
            gr_number=None,
            has_grn=False,
            scenario="missing_grn",
        ),
        dict(
            po_id=_MATCH_PO_ESC,
            po_number="PO-MATCH-ESC",
            inv_id=_MATCH_INV_ESC,
            inv_number="INV-MATCH-ESC",
            amount=1200.00,  # +20% → escalate
            match_status="PENDING",
            gr_id=_MATCH_GR_ESC,
            gr_number="GR-MATCH-ESC",
            has_grn=True,
            scenario="escalate",
        ),
    ]

    for sc in match_scenarios:
        _upsert(
            session,
            "purchase_orders",
            dict(
                id=sc["po_id"],
                tenant_id=SEED_TENANT_ID,
                po_number=sc["po_number"],
                supplier_id=_DEMO_SUPPLIER_ID,
                status="SENT",
                created_at=_now(),
                updated_at=_now(),
                created_by=buyer_id,
                updated_by=buyer_id,
                is_active=True,
            ),
            conflict_col="po_number",
        )
        _upsert(
            session,
            "purchase_order_items",
            dict(
                id=_uuid(f"po_item:{sc['scenario']}"),
                tenant_id=SEED_TENANT_ID,
                po_id=sc["po_id"],
                description=f"3-way match demo item ({sc['scenario']})",
                quantity=10,
                price=100.00,
                created_at=_now(),
                updated_at=_now(),
                created_by=buyer_id,
                updated_by=buyer_id,
                is_active=True,
            ),
            conflict_col="id",
        )
        if sc["has_grn"]:
            _upsert(
                session,
                "receipts",
                dict(
                    id=sc["gr_id"],
                    tenant_id=SEED_TENANT_ID,
                    receipt_number=sc["gr_number"],
                    po_id=sc["po_id"],
                    status="completed",
                    received_date=date(2026, 7, 1),
                    quantity_received=10,
                    amount_received=1000.00,
                    created_at=_now(),
                    updated_at=_now(),
                    created_by=buyer_id,
                    updated_by=buyer_id,
                    is_active=True,
                ),
                conflict_col="receipt_number",
            )
        _upsert(
            session,
            "invoices",
            dict(
                id=sc["inv_id"],
                tenant_id=SEED_TENANT_ID,
                invoice_number=sc["inv_number"],
                po_id=sc["po_id"],
                amount=sc["amount"],
                match_status=sc["match_status"],
                invoice_date=date(2026, 7, 10),
                due_date=date(2026, 8, 10),
                extras=json.dumps({
                    "demo_scenario": sc["scenario"],
                    "supplier_reference": f"DEMO-{sc['scenario'].upper()}",
                }),
                created_at=_now(),
                updated_at=_now(),
                created_by=finance_id,
                updated_by=finance_id,
                is_active=True,
            ),
            conflict_col="invoice_number",
        )

    # Backfill qty on demo receipts that were seeded before the column existed
    session.execute(
        text(
            """
            UPDATE receipts
            SET quantity_received = COALESCE(quantity_received, 150),
                amount_received = COALESCE(amount_received, 3000)
            WHERE receipt_number = 'GR-260710-00001'
            """
        ),
    )
    # Keep match demo invoices PENDING so the live walkthrough can run Match
    session.execute(
        text(
            """
            UPDATE invoices
            SET match_status = 'PENDING',
                amount = CASE invoice_number
                    WHEN 'INV-MATCH-CLEAN' THEN 1000
                    WHEN 'INV-MATCH-AUTO' THEN 1060
                    WHEN 'INV-MATCH-NOGRN' THEN 1000
                    WHEN 'INV-MATCH-ESC' THEN 1200
                    ELSE amount
                END,
                extras = COALESCE(extras, '{}'::jsonb) - 'match_result'
            WHERE invoice_number LIKE 'INV-MATCH-%'
            """
        ),
    )
    session.commit()

    print(
        f"  ✓ {len(suppliers_data)} suppliers, 1 contract, {len(pr_defs)} PRs, "
        f"{len(po_defs) + 1 + len(match_scenarios)} POs, "
        f"{1 + sum(1 for s in match_scenarios if s['has_grn'])} receipts, "
        f"{len(invoice_defs) + len(match_scenarios)} invoices seeded "
        f"(incl. {len(match_scenarios)} 3-way match demos)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════════


def _upsert(
    session: Session,
    table: str,
    data: dict[str, Any],
    conflict_col: str = "id",
) -> None:
    """Idempotent insert — skip if a row with the given conflict column exists."""
    existing = session.execute(
        text(f"SELECT 1 FROM {table} WHERE {conflict_col} = :val LIMIT 1"),
        {"val": data[conflict_col]},
    ).scalar()
    if existing:
        return
    cols = ", ".join(data.keys())
    placeholders = ", ".join(f":{k}" for k in data)
    session.execute(
        text(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"),
        data,
    )


# ═══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os
    import sys

    # Allow the backend directory to be importable
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://opens2p:opens2p@localhost:5432/opens2p_dev",
    )
    engine = create_engine(db_url)
    seed_database(engine)
    print("🎉 OpenS2P seed complete.")

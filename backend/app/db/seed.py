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
_DEMO_CONTRACT_ID = _uuid("contract:acme-2026")
_DEMO_PR_ID = _uuid("pr:2026-001")
_DEMO_PO_ID = _uuid("po:2026-001")
_DEMO_INVOICE_ID = _uuid("invoice:inv-2026-001")


def _seed_demo_data(session: Session) -> None:
    buyer_id = _uuid("user:buyer")
    approver_id = _uuid("user:approver")
    finance_id = _uuid("user:finance")

    # ── Supplier ─────────────────────────────────────────────────────────
    _upsert(
        session,
        "suppliers",
        dict(
            id=_DEMO_SUPPLIER_ID,
            tenant_id=SEED_TENANT_ID,
            supplier_number="SUP-00001",
            supplier_name="Acme Industrial Supplies Co.",
            status="APPROVED",
            risk_score=15.00,
            description="Leading supplier of industrial components and MRO supplies",
            address="100 Innovation Drive, Chicago, IL 60601, United States",
            extras=json.dumps({
                "payment_terms": "NET30",
                "delivery_lead_days": 10,
                "certifications": ["ISO_9001", "ISO_14001"],
            }),
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

    # ── Purchase Requisition ─────────────────────────────────────────────
    _upsert(
        session,
        "purchase_requisitions",
        dict(
            id=_DEMO_PR_ID,
            tenant_id=SEED_TENANT_ID,
            pr_number="PR-2026-00001",
            status="APPROVED",
            requester_id=_uuid("user:requester"),
            description="Q2 MRO supply order — safety equipment and tools",
            created_at=_now(),
            updated_at=_now(),
            created_by=_uuid("user:requester"),
            updated_by=approver_id,
            is_active=True,
        ),
        conflict_col="pr_number",
    )

    # PR items
    pr_items = [
        dict(
            id=_uuid("pr_item:safety-helmets"),
            requisition_id=_DEMO_PR_ID,
            description="Safety helmets (ANSI Z89.1 certified)",
            quantity=50,
            unit_price=34.50,
        ),
        dict(
            id=_uuid("pr_item:safety-goggles"),
            requisition_id=_DEMO_PR_ID,
            description="Industrial safety goggles, anti-fog",
            quantity=100,
            unit_price=12.75,
        ),
    ]
    for item in pr_items:
        _upsert(
            session,
            "purchase_requisition_items",
            dict(
                id=item["id"],
                tenant_id=SEED_TENANT_ID,
                requisition_id=item["requisition_id"],
                description=item["description"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                created_at=_now(),
                updated_at=_now(),
                created_by=_uuid("user:requester"),
                updated_by=_uuid("user:requester"),
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
            po_number="PO-2026-00001",
            supplier_id=_DEMO_SUPPLIER_ID,
            status="CONFIRMED",
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

    # ── Invoice ──────────────────────────────────────────────────────────
    _upsert(
        session,
        "invoices",
        dict(
            id=_DEMO_INVOICE_ID,
            tenant_id=SEED_TENANT_ID,
            invoice_number="INV-2026-00001",
            po_id=_DEMO_PO_ID,
            amount=2975.00,
            match_status="MATCHED",
            invoice_date=date(2026, 3, 15),
            due_date=date(2026, 4, 14),
            extras=json.dumps({
                "supplier_reference": "ACM-INV-2026-0315",
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

    print("  ✓ Demo supplier, contract, PR, PO, invoice seeded")


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

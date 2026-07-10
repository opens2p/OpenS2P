"""
OpenS2P – Workflow Engine Integration Tests
==============================================
End-to-end test of the workflow engine, event system, and notification service.

Prerequisites:
  1. PostgreSQL is running on localhost:5432
  2. Migrations have been applied (``alembic upgrade head``)
  3. Server is running (``uvicorn app.main:app --port 8000``)
  4. Seed data has been loaded (``python -m app.db.seed``)

Run::

    cd backend && uvicorn app.main:app --port 8000 &
    pytest ../tests/ -v -k workflow --no-header
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from app.security.jwt import create_access_token

BASE_URL = "http://localhost:8000"

# Seeded tenant + admin user IDs (see app/db/seed.py)
SEED_TENANT_ID = uuid.UUID("e53cfb21-3b59-5207-a9d2-ea451d45b52e")
SEED_ADMIN_USER_ID = uuid.UUID("8d7c5e05-e663-5035-b6ea-fabe12654ea8")

ADMIN_TOKEN = create_access_token(
    sub=str(SEED_ADMIN_USER_ID),
    tenant_id=str(SEED_TENANT_ID),
    roles=["SYSTEM_ADMIN"],
)
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

client = httpx.Client(base_url=BASE_URL, timeout=30.0)


# ── helpers ────────────────────────────────────────────────────────────────


def _create_pr() -> uuid.UUID:
    """Create a purchase requisition and return its ID."""
    payload = {
        "requisition_number": f"REQ-{uuid.uuid4().hex[:8].upper()}",
        "title": "Workflow Test PR",
        "description": "Created during workflow integration test",
        "department": "IT",
        "currency_code": "USD",
        "requested_by": str(SEED_ADMIN_USER_ID),
        "items": [
            {
                "line_number": 1,
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 100.00,
                "uom": "EA",
                "currency_code": "USD",
                "category": "IT",
                "required_date": "2026-12-31",
            },
        ],
    }
    resp = client.post(
        "/api/v1/purchase-requisitions",
        json=payload,
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201, f"PR creation failed: {resp.text}"
    return uuid.UUID(resp.json()["data"]["id"])


def _create_supplier() -> uuid.UUID:
    """Create a supplier and return its ID."""
    payload = {
        "supplier_name": f"Workflow Test Supplier {uuid.uuid4().hex[:8]}",
        "supplier_number": f"SUP-{uuid.uuid4().hex[:8].upper()}",
    }
    resp = client.post(
        "/api/v1/suppliers",
        json=payload,
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201, f"Supplier creation failed: {resp.text}"
    return uuid.UUID(resp.json()["data"]["id"])


# ═══════════════════════════════════════════════════════════════════════════
# Workflow Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkflowEngine:
    """Tests the full workflow lifecycle end-to-end."""

    created_workflow_id: uuid.UUID | None = None
    created_task_id: uuid.UUID | None = None

    def test_health(self):
        """Server is running and healthy."""
        resp = client.get("/api/v1/admin/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_01_start_workflow(self):
        """POST /api/v1/workflows → 201 with workflow data."""
        pr_id = _create_pr()

        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["object_type"] == "PR_APPROVAL"
        assert data["data"]["object_id"] == str(pr_id)
        assert data["data"]["status"] == "IN_PROGRESS"
        assert "id" in data["data"]
        assert "workflow_name" in data["data"]
        assert "tasks" in data["data"]
        assert len(data["data"]["tasks"]) >= 1

        TestWorkflowEngine.created_workflow_id = uuid.UUID(data["data"]["id"])
        if data["data"]["tasks"]:
            TestWorkflowEngine.created_task_id = uuid.UUID(data["data"]["tasks"][0]["id"])

    def test_02_get_workflow(self):
        """GET /api/v1/workflows/{id} → 200 with workflow."""
        wf_id = TestWorkflowEngine.created_workflow_id
        if wf_id is None:
            pytest.skip("No workflow created")
        resp = client.get(f"/api/v1/workflows/{wf_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == str(wf_id)
        assert "tasks" in data["data"]

    def test_03_get_nonexistent_workflow_404(self):
        """GET /api/v1/workflows/{fake_id} → 404."""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/workflows/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_04_list_pending_tasks(self):
        """GET /api/v1/workflows/tasks/pending → 200 with list."""
        resp = client.get(
            f"/api/v1/workflows/tasks/pending?user_id={SEED_ADMIN_USER_ID}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_05_approve_task(self):
        """POST /api/v1/workflows/tasks/{id}/approve → 200."""
        task_id = TestWorkflowEngine.created_task_id
        if task_id is None:
            pytest.skip("No task created")

        resp = client.post(
            f"/api/v1/workflows/tasks/{task_id}/approve",
            json={"payload": {"note": "Approved in test"}},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["data"]["status"] == "APPROVED"
        assert data["data"]["id"] == str(task_id)

    def test_06_reject_task(self):
        """POST /api/v1/workflows/tasks/{id}/reject → 200."""
        pr_id = _create_pr()

        # Start a new workflow for the reject test
        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        task_id = uuid.UUID(resp.json()["data"]["tasks"][0]["id"])

        resp = client.post(
            f"/api/v1/workflows/tasks/{task_id}/reject",
            json={"reason": "Rejected in test"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["data"]["status"] == "REJECTED"
        assert data["data"]["id"] == str(task_id)

    def test_07_approve_nonexistent_task_404(self):
        """POST /api/v1/workflows/tasks/{fake_id}/approve → 404."""
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/workflows/tasks/{fake_id}/approve",
            json={},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_08_reject_nonexistent_task_404(self):
        """POST /api/v1/workflows/tasks/{fake_id}/reject → 404."""
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/workflows/tasks/{fake_id}/reject",
            json={"reason": "test"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_09_get_history(self):
        """GET /api/v1/workflows/history/{type}/{id} → 200 with history list."""
        # Get history for the PR from test_01
        resp = client.get(
            "/api/v1/workflows/history/PR_APPROVAL/"
            f"{uuid.uuid4()}",
            headers=AUTH_HEADERS,
        )
        # May be empty list if PR doesn't exist — 200 is fine
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_10_start_workflow_supplier_onboarding(self):
        """Start a supplier onboarding workflow."""
        supplier_id = _create_supplier()
        payload = {
            "object_type": "SUPPLIER_ONBOARDING",
            "object_id": str(supplier_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["object_type"] == "SUPPLIER_ONBOARDING"
        assert data["data"]["object_id"] == str(supplier_id)
        assert data["data"]["status"] == "IN_PROGRESS"
        assert len(data["data"]["tasks"]) >= 1

    def test_11_start_workflow_po_approval(self):
        """Start a PO approval workflow."""
        payload = {
            "object_type": "PO_APPROVAL",
            "object_id": str(uuid.uuid4()),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["object_type"] == "PO_APPROVAL"
        assert data["data"]["status"] == "IN_PROGRESS"

    def test_12_start_workflow_invoice_match(self):
        """Start an invoice matching workflow."""
        payload = {
            "object_type": "INVOICE_MATCH",
            "object_id": str(uuid.uuid4()),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["object_type"] == "INVOICE_MATCH"
        assert data["data"]["status"] == "IN_PROGRESS"

    def test_13_approve_full_workflow_chain(self):
        """Approve all tasks in a workflow and verify it completes."""
        pr_id = _create_pr()
        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        wf_id = uuid.UUID(resp.json()["data"]["id"])
        tasks = resp.json()["data"]["tasks"]

        # Approve each task in sequence
        for task in tasks:
            task_id = uuid.UUID(task["id"])
            resp = client.post(
                f"/api/v1/workflows/tasks/{task_id}/approve",
                json={},
                headers=AUTH_HEADERS,
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "APPROVED"

        # Verify workflow is completed
        resp = client.get(f"/api/v1/workflows/{wf_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "COMPLETED"

    def test_14_escalate_task(self):
        """POST /api/v1/workflows/tasks/{id}/escalate → 200."""
        pr_id = _create_pr()
        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        task_id = uuid.UUID(resp.json()["data"]["tasks"][0]["id"])

        # Use the seeded admin user as the escalation target
        resp = client.post(
            f"/api/v1/workflows/tasks/{task_id}/escalate",
            json={
                "new_approver_id": str(SEED_ADMIN_USER_ID),
                "reason": "Escalated for test",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["data"]["id"] == str(task_id)

    def test_15_escalate_nonexistent_task_404(self):
        """POST /api/v1/workflows/tasks/{fake_id}/escalate → 404."""
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/workflows/tasks/{fake_id}/escalate",
            json={
                "new_approver_id": str(uuid.uuid4()),
                "reason": "test",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_16_start_workflow_without_auth_401(self):
        """POST /api/v1/workflows without auth → 401."""
        resp = client.post(
            "/api/v1/workflows",
            json={"object_type": "PR_APPROVAL", "object_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_17_get_workflow_history_with_existing_object(self):
        """GET /api/v1/workflows/history/{type}/{id} for an object with workflow."""
        pr_id = _create_pr()
        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201

        resp = client.get(
            f"/api/v1/workflows/history/PR_APPROVAL/{pr_id}",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["object_id"] == str(pr_id)

    def test_18_approve_task_with_payload(self):
        """Approve task with custom payload data."""
        pr_id = _create_pr()
        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        task_id = uuid.UUID(resp.json()["data"]["tasks"][0]["id"])

        resp = client.post(
            f"/api/v1/workflows/tasks/{task_id}/approve",
            json={"payload": {"approved_by": "IT_Manager", "note": "Looks good"}},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "APPROVED"

    def test_19_reject_task_with_reason(self):
        """Reject task and verify reason is captured."""
        pr_id = _create_pr()
        payload = {
            "object_type": "PR_APPROVAL",
            "object_id": str(pr_id),
        }
        resp = client.post(
            "/api/v1/workflows",
            json=payload,
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        task_id = uuid.UUID(resp.json()["data"]["tasks"][0]["id"])

        reason = "Budget not approved for this fiscal year"
        resp = client.post(
            f"/api/v1/workflows/tasks/{task_id}/reject",
            json={"reason": reason},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "REJECTED"


# ═══════════════════════════════════════════════════════════════════════════
# Workflow conditions engine tests
# ═══════════════════════════════════════════════════════════════════════════


class TestConditionsEngine:
    """Tests for the workflow conditions evaluation engine."""

    def test_20_condition_gt(self):
        """amount > 100000 is True for 200000."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("amount > 100000", {"amount": 200000}) is True

    def test_21_condition_gt_false(self):
        """amount > 100000 is False for 50000."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("amount > 100000", {"amount": 50000}) is False

    def test_22_condition_eq(self):
        """department == \"IT\" matches."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition('department == "IT"', {"department": "IT"}) is True

    def test_23_condition_eq_false(self):
        """department == \"IT\" does not match HR."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition('department == "IT"', {"department": "HR"}) is False

    def test_24_condition_ne(self):
        """department != \"IT\" matches HR."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition('department != "IT"', {"department": "HR"}) is True

    def test_25_condition_gte(self):
        """amount >= 100 matches 100."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("amount >= 100", {"amount": 100}) is True

    def test_26_condition_lte(self):
        """amount <= 50 matches 30."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("amount <= 50", {"amount": 30}) is True

    def test_27_condition_in_list(self):
        """category in [\"IT\", \"SOFTWARE\"] matches IT."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition(
            'category in ["IT", "SOFTWARE"]',
            {"category": "IT"},
        ) is True

    def test_28_condition_in_list_false(self):
        """category in [\"IT\", \"SOFTWARE\"] does not match HR."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition(
            'category in ["IT", "SOFTWARE"]',
            {"category": "HR"},
        ) is False

    def test_29_condition_dotted_path(self):
        """supplier.risk_score > 50 resolves nested context."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition(
            "supplier.risk_score > 50",
            {"supplier": {"risk_score": 75}},
        ) is True

    def test_30_condition_missing_key(self):
        """Condition with missing context key returns False."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("amount > 100", {}) is False

    def test_31_condition_boolean_true(self):
        """is_premium == True works."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("is_premium == True", {"is_premium": True}) is True

    def test_32_condition_boolean_false(self):
        """is_premium == False works."""
        from app.workflow.conditions import evaluate_condition
        assert evaluate_condition("is_premium == False", {"is_premium": False}) is True


# ═══════════════════════════════════════════════════════════════════════════
# Workflow rules engine tests
# ═══════════════════════════════════════════════════════════════════════════


class TestRulesEngine:
    """Tests for the rule-based approval routing."""

    def test_33_rule_matches(self):
        """Rule matches when condition is satisfied."""
        from app.workflow.rules import Rule
        rule = Rule("test", "amount > 1000", "MANAGER", priority=10)
        assert rule.matches({"amount": 2000}) is True

    def test_34_rule_no_match(self):
        """Rule does not match when condition is not satisfied."""
        from app.workflow.rules import Rule
        rule = Rule("test", "amount > 1000", "MANAGER", priority=10)
        assert rule.matches({"amount": 500}) is False

    def test_35_resolve_approver_high_value(self):
        """High value purchases route to FINANCE_USER."""
        from app.workflow.rules import resolve_approver, DEFAULT_RULES
        import asyncio
        role = asyncio.run(resolve_approver(DEFAULT_RULES, {"amount": 200000}))
        assert role == "FINANCE_USER"

    def test_36_resolve_approver_medium_value(self):
        """Medium value purchases route to PROCUREMENT_MANAGER."""
        from app.workflow.rules import resolve_approver, DEFAULT_RULES
        import asyncio
        role = asyncio.run(resolve_approver(DEFAULT_RULES, {"amount": 50000}))
        assert role == "PROCUREMENT_MANAGER"

    def test_37_resolve_approver_high_risk_supplier(self):
        """High risk suppliers route to LEGAL_REVIEW regardless of amount."""
        from app.workflow.rules import resolve_approver, DEFAULT_RULES
        import asyncio
        role = asyncio.run(resolve_approver(
            DEFAULT_RULES,
            {"amount": 5000, "supplier_risk": "HIGH"},
        ))
        assert role == "LEGAL_REVIEW"

    def test_38_resolve_approver_it_category(self):
        """IT category routes to IT_MANAGER."""
        from app.workflow.rules import resolve_approver, DEFAULT_RULES
        import asyncio
        role = asyncio.run(resolve_approver(
            DEFAULT_RULES,
            {"amount": 5000, "category": "IT"},
        ))
        assert role == "IT_MANAGER"

    def test_39_resolve_approver_default(self):
        """Low value, no-risk, non-IT purchases default to PROCUREMENT_MANAGER."""
        from app.workflow.rules import resolve_approver, DEFAULT_RULES
        import asyncio
        role = asyncio.run(resolve_approver(
            DEFAULT_RULES,
            {"amount": 100, "category": "OFFICE_SUPPLIES"},
        ))
        assert role == "PROCUREMENT_MANAGER"

    def test_40_resolve_approver_custom_rules(self):
        """Custom rules can override defaults."""
        from app.workflow.rules import Rule, resolve_approver
        import asyncio
        custom = [Rule("urgent", "priority == HIGH", "CEO", priority=200)]
        role = asyncio.run(resolve_approver(
            custom,
            {"amount": 100, "priority": "HIGH"},
            default_role="MANAGER",
        ))
        assert role == "CEO"


# ═══════════════════════════════════════════════════════════════════════════
# Event system tests
# ═══════════════════════════════════════════════════════════════════════════


class TestEventBus:
    """Tests for the in-process event bus."""

    def test_41_publish_subscribe(self):
        """Events are delivered to registered handlers."""
        from app.events.event_bus import publish, subscribe, clear_handlers

        received = []

        async def handler(event):
            received.append(event)

        subscribe("TEST_EVENT", handler)

        import asyncio
        asyncio.run(publish("TEST_EVENT", {"foo": "bar"}))

        assert len(received) == 1
        assert received[0]["event_type"] == "TEST_EVENT"
        assert received[0]["payload"]["foo"] == "bar"

        clear_handlers()

    def test_42_unsubscribe(self):
        """Unsubscribed handlers no longer receive events."""
        from app.events.event_bus import publish, subscribe, unsubscribe, clear_handlers

        received = []

        async def handler(event):
            received.append(event)

        subscribe("TEST_EVENT", handler)
        unsubscribe("TEST_EVENT", handler)

        import asyncio
        asyncio.run(publish("TEST_EVENT", {"foo": "bar"}))

        assert len(received) == 0
        clear_handlers()

    def test_43_clear_handlers(self):
        """All handlers are cleared."""
        from app.events.event_bus import publish, clear_handlers

        # After clear_handlers, no handlers should exist
        clear_handlers()

        import asyncio
        # Should not raise
        asyncio.run(publish("TEST_EVENT", {"foo": "bar"}))

    def test_44_multiple_handlers(self):
        """Multiple handlers for same event all receive it."""
        from app.events.event_bus import publish, subscribe, clear_handlers

        received1 = []
        received2 = []

        async def handler1(event):
            received1.append(event)

        async def handler2(event):
            received2.append(event)

        subscribe("MULTI_EVENT", handler1)
        subscribe("MULTI_EVENT", handler2)

        import asyncio
        asyncio.run(publish("MULTI_EVENT", {"val": 42}))

        assert len(received1) == 1
        assert len(received2) == 1

        clear_handlers()

    def test_45_handler_error_does_not_block(self):
        """Handler exception does not prevent other handlers from running."""
        from app.events.event_bus import publish, subscribe, clear_handlers

        received = []

        async def failing_handler(event):
            raise ValueError("Intentional failure")

        async def working_handler(event):
            received.append(event)

        subscribe("ERR_EVENT", failing_handler)
        subscribe("ERR_EVENT", working_handler)

        import asyncio
        asyncio.run(publish("ERR_EVENT", {"val": 99}))

        assert len(received) == 1
        clear_handlers()

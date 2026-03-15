from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import reset_settings_cache
from app.core.dependencies import reset_dependency_caches
from app.main import create_app


def _client() -> TestClient:
    reset_settings_cache()
    reset_dependency_caches()
    return TestClient(create_app())


def test_bootstrap_and_transactions_and_goals_flow() -> None:
    client = _client()
    assert client.post("/api/v1/admin/bootstrap").status_code == 200
    tx = client.post(
        "/api/v1/transactions",
        json={"type": "OUT", "amount": 500000, "currency": "VND", "jarCode": "HuongThu", "note": "manual"},
    )
    assert tx.status_code == 201
    listed = client.get("/api/v1/transactions")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1
    goal = client.post("/api/v1/goals", json={"name": "Mua xe SH", "targetAmount": 100000000, "status": "active"})
    assert goal.status_code == 201
    rules = client.post(
        "/api/v1/fixed-cost-rules",
        json={"name": "Rent", "expectedAmount": 5000000, "windowStartDay": 1, "windowEndDay": 5, "isActive": True},
    )
    assert rules.status_code == 201


def test_dashboard_and_ingestion_routes() -> None:
    client = _client()
    ingest = client.post("/api/v1/ingestion/chat", json={"rawInput": "di nhau voi phong 500k #team", "source": "chat"})
    assert ingest.status_code == 201
    parsed = client.get("/api/v1/parsed-receipts")
    assert parsed.status_code == 200
    assert len(parsed.json()["items"]) == 1
    receipt_id = parsed.json()["items"][0]["receipt"]["id"]
    detail = client.get(f"/api/v1/parsed-receipts/{receipt_id}")
    assert detail.status_code == 200
    assert detail.json()["receipt"]["transactionId"] == ingest.json()["transactionId"]
    assert detail.json()["transaction"]["status"] == "draft"
    confirm = client.post(f"/api/v1/parsed-receipts/{receipt_id}/confirm", json={"actor": "tester"})
    assert confirm.status_code == 200
    assert confirm.json()["transaction"]["status"] == "confirmed"
    undo = client.post(f"/api/v1/parsed-receipts/{receipt_id}/undo", json={"actor": "tester"})
    assert undo.status_code == 200
    assert undo.json()["transaction"]["status"] == "reverted"
    summary = client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    reports = client.get("/api/v1/dashboard/reports")
    assert reports.status_code == 200
    monthly = client.post("/api/v1/dashboard/reports/monthly", json={"trigger": "manual"})
    assert monthly.status_code == 201


def test_parsed_receipt_detail_returns_404_for_unknown_id() -> None:
    client = _client()
    response = client.get("/api/v1/parsed-receipts/RCPT-missing")
    assert response.status_code == 404


def test_transaction_correct_and_undo() -> None:
    client = _client()
    created = client.post("/api/v1/transactions", json={"type": "OUT", "amount": 200000, "currency": "VND", "jarCode": "ThietYeu", "note": "original"})
    tx_id = created.json()["id"]
    corrected = client.post(
        f"/api/v1/transactions/{tx_id}/correct",
        json={
            "occurredAt": created.json()["occurredAt"],
            "type": "OUT",
            "amount": 200000,
            "currency": "VND",
            "jarCode": "HuongThu",
            "note": "corrected",
            "status": "confirmed",
            "reason": "wrong category",
            "actor": "user",
        },
    )
    assert corrected.status_code == 200
    undone = client.post(f"/api/v1/transactions/{tx_id}/undo", json={"reason": "mist entry", "actor": "user"})
    assert undone.status_code == 200
    assert undone.json()["status"] == "reverted"

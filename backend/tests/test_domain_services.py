from __future__ import annotations

from datetime import UTC, datetime

from app.ai.client import NoopClient
from app.core.runtime import Clock, TransactionIDGenerator
from app.domain.goals.model import CreateInput as CreateGoalInput
from app.domain.goals.service import GoalService
from app.domain.ingestion.model import IngestInput
from app.domain.ingestion.model import ReviewCorrectInput
from app.domain.ingestion.review_service import ParsedReceiptReviewService
from app.domain.ingestion.service import IngestionService, parse_suggestion
from app.domain.metrics.service import MetricsService
from app.domain.reports.model import GenerateInput
from app.domain.reports.service import ReportsService, parse_generated_report
from app.domain.rules.model import CreateFixedCostRuleInput
from app.domain.rules.service import RulesService
from app.domain.transactions.model import CreateInput, UpdateInput
from app.domain.transactions.service import TransactionService
from app.infrastructure.memory.repositories import (
    MemoryAuditLogger,
    MemoryGoalsRepository,
    MemoryParsedReceiptsRepository,
    MemoryReportsRepository,
    MemoryRulesRepository,
    MemoryTransactionRepository,
)


class FakeClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC)


class FakeIDs(TransactionIDGenerator):
    def new_transaction_id(self) -> str:
        return "TX-001"


def test_transaction_defaults_and_audit() -> None:
    tx_repo = MemoryTransactionRepository()
    audit = MemoryAuditLogger()
    service = TransactionService(tx_repo, audit, FakeIDs(), FakeClock())
    created = service.create(CreateInput(type="OUT", amount=500000))
    assert created.id == "TX-001"
    assert created.currency == "VND"
    corrected = service.correct(
        "TX-001",
        UpdateInput(
            occurredAt=created.occurred_at,
            type="OUT",
            amount=500000,
            currency="VND",
            jarCode="HuongThu",
            note="fixed",
        ),
        "wrong category",
        "user",
    )
    assert corrected.jar_code == "HuongThu"
    assert len(audit.entries) == 1
    undone = service.undo("TX-001", "mist entry", "user")
    assert undone.status == "reverted"


def test_goals_rules_and_metrics_summary() -> None:
    clock = FakeClock()
    tx_service = TransactionService(MemoryTransactionRepository(), MemoryAuditLogger(), FakeIDs(), clock)
    tx_service.create(CreateInput(type="OUT", amount=300000, occurredAt=clock.now()))
    tx_service.create(CreateInput(type="IN", amount=20_000_000, occurredAt=datetime(2026, 3, 10, 9, 0, 0, tzinfo=UTC)))
    tx_service.create(CreateInput(type="TRANSFER", amount=5_000_000, goalName="Mua xe SH", occurredAt=datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC)))
    goals = GoalService(MemoryGoalsRepository(), clock)
    goals.create(CreateGoalInput(name="Mua xe SH", targetAmount=100_000_000, startDate=datetime(2026, 1, 1, tzinfo=UTC)))
    rules = RulesService(MemoryRulesRepository())
    rules.create_fixed_cost_rule(CreateFixedCostRuleInput(name="Rent", expectedAmount=5_000_000, windowStartDay=1, windowEndDay=5, isActive=True))
    summary = MetricsService(tx_service, goals, rules, clock).summary()
    assert summary.sts.label == "STS Today"
    assert len(summary.baselines) == 3
    assert summary.operating_posture.status


def test_ingestion_and_reports() -> None:
    clock = FakeClock()
    tx_service = TransactionService(MemoryTransactionRepository(), MemoryAuditLogger(), FakeIDs(), clock)
    goals = GoalService(MemoryGoalsRepository(), clock)
    rules = RulesService(MemoryRulesRepository())
    receipts = MemoryParsedReceiptsRepository()
    ingestion = IngestionService(tx_service, receipts, NoopClient(), clock, "", "", "none")
    result = ingestion.ingest_chat(IngestInput(rawInput="di nhau 500k #team", source="chat"))
    assert result.transaction_id == "TX-001"
    assert receipts.items[0].validation_note
    metrics = MetricsService(tx_service, goals, rules, clock)
    reports = ReportsService(MemoryReportsRepository(), metrics, tx_service, goals, rules, NoopClient(), clock, "UTC", "", "", "", "daily", "monthly")
    snapshot = reports.dashboard()
    assert snapshot.daily.kind == "daily"
    monthly = reports.generate_monthly(GenerateInput(trigger="manual"))
    assert monthly.kind == "monthly"


def test_parsed_receipt_review_links_draft_transaction() -> None:
    clock = FakeClock()
    tx_repo = MemoryTransactionRepository()
    tx_service = TransactionService(tx_repo, MemoryAuditLogger(), FakeIDs(), clock)
    receipts = MemoryParsedReceiptsRepository()
    ingestion = IngestionService(tx_service, receipts, NoopClient(), clock, "", "", "none")
    result = ingestion.ingest_chat(IngestInput(rawInput="mua sach 200k #study", source="chat"))

    review = ParsedReceiptReviewService(receipts, tx_service)
    items = review.list()

    assert len(items) == 1
    assert items[0].receipt.id == result.receipt.id
    assert items[0].transaction is not None
    assert items[0].transaction.id == result.transaction_id
    assert items[0].transaction.status == "draft"


def test_parsed_receipt_review_actions_confirm_correct_and_undo() -> None:
    clock = FakeClock()
    tx_repo = MemoryTransactionRepository()
    tx_service = TransactionService(tx_repo, MemoryAuditLogger(), FakeIDs(), clock)
    receipts = MemoryParsedReceiptsRepository()
    ingestion = IngestionService(tx_service, receipts, NoopClient(), clock, "", "", "none")
    result = ingestion.ingest_chat(IngestInput(rawInput="an trua 150k #meal", source="chat"))

    review = ParsedReceiptReviewService(receipts, tx_service)
    confirmed = review.confirm(result.receipt.id, "looks good", "reviewer")
    assert confirmed.transaction is not None
    assert confirmed.transaction.status == "confirmed"

    corrected = review.correct(
        result.receipt.id,
        ReviewCorrectInput(
            occurredAt=confirmed.transaction.occurred_at,
            type="OUT",
            amount=175000,
            currency="VND",
            jarCode="ThietYeu",
            note="an trua cap nhat",
            reason="fix amount",
            actor="reviewer",
        ),
    )
    assert corrected.transaction is not None
    assert corrected.transaction.amount == 175000

    undone = review.undo(result.receipt.id, "duplicate", "reviewer")
    assert undone.transaction is not None
    assert undone.transaction.status == "reverted"


def test_llm_json_parsing_uses_regex_extraction_for_ingestion_and_reports() -> None:
    suggestion = parse_suggestion('Before json\n```json\n{"action":"OUT","amount":500000,"jar_category":"HuongThu"}\n```\nafter')
    assert suggestion["amount"] == 500000

    report = parse_generated_report('Narrative first {"title":"Daily","summary":"ok","body":"watch spend","verdict":"stable","status":"watch"}')
    assert report["title"] == "Daily"

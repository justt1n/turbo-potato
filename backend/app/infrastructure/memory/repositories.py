from __future__ import annotations

from app.domain.goals.model import Goal
from app.domain.ingestion.model import ParsedReceipt
from app.domain.reports.model import Report
from app.domain.rules.model import FixedCostRule
from app.domain.transactions.model import AuditEntry, Transaction


class MemoryTransactionRepository:
    def __init__(self) -> None:
        self.items: list[Transaction] = []

    def create_transaction(self, tx: Transaction) -> Transaction:
        self.items.append(tx)
        return tx

    def get_transaction(self, tx_id: str) -> Transaction:
        for item in self.items:
            if item.id == tx_id:
                return item
        raise ValueError(f"transaction {tx_id} not found")

    def update_transaction(self, tx: Transaction) -> Transaction:
        for index, item in enumerate(self.items):
            if item.id == tx.id:
                self.items[index] = tx
                return tx
        raise ValueError(f"transaction {tx.id} not found")

    def list_transactions(self) -> list[Transaction]:
        return list(self.items)


class MemoryAuditLogger:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def log(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class MemoryGoalsRepository:
    def __init__(self) -> None:
        self.items: list[Goal] = []

    def create_goal(self, goal: Goal) -> Goal:
        self.items.append(goal)
        return goal

    def list_goals(self) -> list[Goal]:
        return list(self.items)


class MemoryRulesRepository:
    def __init__(self) -> None:
        self.items: list[FixedCostRule] = []

    def create_fixed_cost_rule(self, rule: FixedCostRule) -> FixedCostRule:
        self.items.append(rule)
        return rule

    def list_fixed_cost_rules(self) -> list[FixedCostRule]:
        return list(self.items)


class MemoryParsedReceiptsRepository:
    def __init__(self) -> None:
        self.items: list[ParsedReceipt] = []

    def save_parsed_receipt(self, receipt: ParsedReceipt) -> ParsedReceipt:
        self.items.append(receipt)
        return receipt

    def list_parsed_receipts(self) -> list[ParsedReceipt]:
        return list(self.items)

    def get_parsed_receipt(self, receipt_id: str) -> ParsedReceipt:
        for item in self.items:
            if item.id == receipt_id:
                return item
        raise ValueError(f"parsed receipt {receipt_id} not found")


class MemoryReportsRepository:
    def __init__(self) -> None:
        self.items: list[Report] = []

    def save(self, report: Report) -> Report:
        self.items.append(report)
        return report

    def find_by_kind_and_period(self, kind: str, period_key: str) -> Report | None:
        for item in reversed(self.items):
            if item.kind == kind and item.period_key == period_key:
                return item
        return None

    def latest_by_kind(self, kind: str) -> Report | None:
        for item in reversed(self.items):
            if item.kind == kind:
                return item
        return None

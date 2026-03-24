from __future__ import annotations

import json
import time
from datetime import datetime

from app.domain.jars.model import Jar
from app.domain.goals.model import Goal
from app.domain.ingestion.model import ParsedReceipt
from app.domain.reports.model import Report
from app.domain.rules.model import FixedCostRule
from app.domain.sources.model import Source
from app.domain.transactions.model import AuditEntry, Transaction
from app.infrastructure.sheets.types import ValuesAPI


def _stringify(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    return str(value)


def _cell(row: list[object], index: int) -> object:
    if index < len(row):
        return row[index]
    return ""


class GoogleTransactionRepository:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def create_transaction(self, tx: Transaction) -> Transaction:
        self._client.append(self._spreadsheet_id, "Transactions!A:N", [transaction_to_row(tx)])
        return tx

    def get_transaction(self, tx_id: str) -> Transaction:
        rows = self._client.get(self._spreadsheet_id, "Transactions!A2:N")
        for row in rows:
            if row and _stringify(row[0]) == tx_id:
                return transaction_from_row(row)
        raise ValueError(f"transaction {tx_id} not found")

    def update_transaction(self, tx: Transaction) -> Transaction:
        rows = self._client.get(self._spreadsheet_id, "Transactions!A2:N")
        for index, row in enumerate(rows, start=2):
            if row and _stringify(row[0]) == tx.id:
                self._client.update(self._spreadsheet_id, f"Transactions!A{index}:N{index}", [transaction_to_row(tx)])
                return tx
        raise ValueError(f"transaction {tx.id} not found")

    def list_transactions(self) -> list[Transaction]:
        return [transaction_from_row(row) for row in self._client.get(self._spreadsheet_id, "Transactions!A2:N") if row]


class GoogleAuditLogger:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def log(self, entry: AuditEntry) -> None:
        self._client.append(
            self._spreadsheet_id,
            "Audit_Log!A:H",
            [[entry.id, entry.transaction_id, entry.action, entry.previous_value, entry.new_value, entry.reason, entry.actor, entry.created_at.isoformat()]],
        )


class GoogleGoalsRepository:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def create_goal(self, goal: Goal) -> Goal:
        target_date = goal.target_date.isoformat() if goal.target_date else ""
        self._client.append(self._spreadsheet_id, "Goals!A:E", [[goal.name, goal.target_amount, goal.start_date.isoformat(), target_date, goal.status]])
        return goal

    def update_goal(self, current_name: str, goal: Goal) -> Goal:
        rows = self._client.get(self._spreadsheet_id, "Goals!A2:E")
        target_date = goal.target_date.isoformat() if goal.target_date else ""
        for index, row in enumerate(rows, start=2):
            if row and _stringify(row[0]) == current_name:
                self._client.update(
                    self._spreadsheet_id,
                    f"Goals!A{index}:E{index}",
                    [[goal.name, goal.target_amount, goal.start_date.isoformat(), target_date, goal.status]],
                )
                return goal
        raise ValueError(f"goal {current_name} not found")

    def list_goals(self) -> list[Goal]:
        rows = self._client.get(self._spreadsheet_id, "Goals!A2:E")
        out: list[Goal] = []
        for row in rows:
            if not row:
                continue
            out.append(
                Goal(
                    name=_stringify(row[0]),
                    targetAmount=int(_stringify(row[1])),
                    startDate=datetime.fromisoformat(_stringify(row[2])),
                    targetDate=datetime.fromisoformat(_stringify(row[3])) if _stringify(row[3]) else None,
                    status=_stringify(row[4]),
                )
            )
        return out


class GoogleJarsRepository:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def create_jar(self, jar: Jar) -> Jar:
        self._client.append(
            self._spreadsheet_id,
            "Jars!A:G",
            [[jar.code, jar.name, jar.kind, jar.opening_balance, jar.actual_balance, jar.is_active, jar.note]],
        )
        return jar

    def update_jar(self, current_code: str, jar: Jar) -> Jar:
        rows = self._client.get(self._spreadsheet_id, "Jars!A2:G")
        for index, row in enumerate(rows, start=2):
            if row and _stringify(row[0]) == current_code:
                self._client.update(
                    self._spreadsheet_id,
                    f"Jars!A{index}:G{index}",
                    [[jar.code, jar.name, jar.kind, jar.opening_balance, jar.actual_balance, jar.is_active, jar.note]],
                )
                return jar
        raise ValueError(f"jar {current_code} not found")

    def list_jars(self) -> list[Jar]:
        rows = self._client.get(self._spreadsheet_id, "Jars!A2:G")
        out: list[Jar] = []
        for row in rows:
            if not row:
                continue
            out.append(
                Jar(
                    code=_stringify(_cell(row, 0)),
                    name=_stringify(_cell(row, 1)),
                    kind=_stringify(_cell(row, 2)) or "cash",
                    openingBalance=int(_stringify(_cell(row, 3)) or 0),
                    actualBalance=int(_stringify(_cell(row, 4)) or 0),
                    isActive=_stringify(_cell(row, 5)).lower() == "true",
                    note=_stringify(_cell(row, 6)),
                )
            )
        return out


class GoogleRulesRepository:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def create_fixed_cost_rule(self, rule: FixedCostRule) -> FixedCostRule:
        self._client.append(
            self._spreadsheet_id,
            "Fixed_Cost_Rules!A:F",
            [[rule.name, rule.expected_amount, rule.window_start_day, rule.window_end_day, rule.linked_jar_code, rule.is_active]],
        )
        return rule

    def update_fixed_cost_rule(self, current_name: str, rule: FixedCostRule) -> FixedCostRule:
        rows = self._client.get(self._spreadsheet_id, "Fixed_Cost_Rules!A2:F")
        for index, row in enumerate(rows, start=2):
            if row and _stringify(row[0]) == current_name:
                self._client.update(
                    self._spreadsheet_id,
                    f"Fixed_Cost_Rules!A{index}:F{index}",
                    [[rule.name, rule.expected_amount, rule.window_start_day, rule.window_end_day, rule.linked_jar_code, rule.is_active]],
                )
                return rule
        raise ValueError(f"fixed cost rule {current_name} not found")

    def list_fixed_cost_rules(self) -> list[FixedCostRule]:
        rows = self._client.get(self._spreadsheet_id, "Fixed_Cost_Rules!A2:F")
        out: list[FixedCostRule] = []
        for row in rows:
            if not row:
                continue
            out.append(
                FixedCostRule(
                    name=_stringify(row[0]),
                    expectedAmount=int(_stringify(row[1])),
                    windowStartDay=int(_stringify(row[2])),
                    windowEndDay=int(_stringify(row[3])),
                    linkedJarCode=_stringify(row[4]),
                    isActive=_stringify(row[5]).lower() == "true",
                )
            )
        return out


class GoogleSourcesRepository:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def create_source(self, source: Source) -> Source:
        self._client.append(
            self._spreadsheet_id,
            "Sources!A:K",
            [[
                source.code,
                source.name,
                source.kind,
                source.provider,
                source.linked_jar_code,
                source.opening_balance,
                source.actual_balance,
                source.gold_quantity_chi,
                source.gold_price_per_chi,
                source.is_active,
                source.note,
            ]],
        )
        return source

    def update_source(self, current_code: str, source: Source) -> Source:
        rows = self._client.get(self._spreadsheet_id, "Sources!A2:K")
        for index, row in enumerate(rows, start=2):
            if row and _stringify(row[0]) == current_code:
                self._client.update(
                    self._spreadsheet_id,
                    f"Sources!A{index}:K{index}",
                    [[
                        source.code,
                        source.name,
                        source.kind,
                        source.provider,
                        source.linked_jar_code,
                        source.opening_balance,
                        source.actual_balance,
                        source.gold_quantity_chi,
                        source.gold_price_per_chi,
                        source.is_active,
                        source.note,
                    ]],
                )
                return source
        raise ValueError(f"source {current_code} not found")

    def list_sources(self) -> list[Source]:
        rows = self._client.get(self._spreadsheet_id, "Sources!A2:K")
        out: list[Source] = []
        for row in rows:
            if not row:
                continue
            out.append(
                Source(
                    code=_stringify(_cell(row, 0)),
                    name=_stringify(_cell(row, 1)),
                    kind=_stringify(_cell(row, 2)) or "wallet",
                    provider=_stringify(_cell(row, 3)),
                    linkedJarCode=_stringify(_cell(row, 4)),
                    openingBalance=int(_stringify(_cell(row, 5)) or 0),
                    actualBalance=int(_stringify(_cell(row, 6)) or 0),
                    goldQuantityChi=float(_stringify(_cell(row, 7)) or 0),
                    goldPricePerChi=int(_stringify(_cell(row, 8)) or 0),
                    isActive=_stringify(_cell(row, 9)).lower() == "true",
                    note=_stringify(_cell(row, 10)),
                )
            )
        return out


class GoogleParsedReceiptsRepository:
    _read_attempts = 3
    _read_delay_seconds = 0.2

    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def save_parsed_receipt(self, receipt: ParsedReceipt) -> ParsedReceipt:
        self._client.append(
            self._spreadsheet_id,
            "Parsed_Receipts!A:K",
            [[receipt.id, receipt.transaction_id, receipt.raw_input, receipt.regex_amount, ",".join(receipt.regex_tags), receipt.llm_model, receipt.llm_output_json, receipt.validation_note, receipt.confidence, receipt.prompt_source, receipt.created_at.isoformat()]],
        )
        return receipt

    def list_parsed_receipts(self) -> list[ParsedReceipt]:
        rows = self._load_rows()
        return [parsed_receipt_from_row(row) for row in rows if row]

    def get_parsed_receipt(self, receipt_id: str) -> ParsedReceipt:
        for item in self.list_parsed_receipts():
            if item.id == receipt_id:
                return item
        raise ValueError(f"parsed receipt {receipt_id} not found")

    def _load_rows(self) -> list[list[object]]:
        rows: list[list[object]] = []
        for attempt in range(self._read_attempts):
            rows = self._client.get(self._spreadsheet_id, "Parsed_Receipts!A2:K")
            if rows or attempt == self._read_attempts - 1:
                return rows
            time.sleep(self._read_delay_seconds)
        return rows


class GoogleReportsRepository:
    def __init__(self, client: ValuesAPI, spreadsheet_id: str) -> None:
        self._client = client
        self._spreadsheet_id = spreadsheet_id

    def save(self, report: Report) -> Report:
        self._client.append(
            self._spreadsheet_id,
            "Reports!A:L",
            [[report.id, report.kind, report.period_key, report.title, report.summary, report.body, report.verdict, report.status, report.model, report.prompt_source, report.trigger, report.created_at.isoformat()]],
        )
        return report

    def find_by_kind_and_period(self, kind: str, period_key: str) -> Report | None:
        for item in reversed(self._list()):
            if item.kind == kind and item.period_key == period_key:
                return item
        return None

    def latest_by_kind(self, kind: str) -> Report | None:
        for item in reversed(self._list()):
            if item.kind == kind:
                return item
        return None

    def _list(self) -> list[Report]:
        rows = self._client.get(self._spreadsheet_id, "Reports!A2:L")
        out: list[Report] = []
        for row in rows:
            if not row:
                continue
            out.append(
                Report(
                    id=_stringify(row[0]),
                    kind=_stringify(row[1]),
                    periodKey=_stringify(row[2]),
                    title=_stringify(row[3]),
                    summary=_stringify(row[4]),
                    body=_stringify(row[5]),
                    verdict=_stringify(row[6]),
                    status=_stringify(row[7]),
                    model=_stringify(row[8]),
                    promptSource=_stringify(row[9]),
                    trigger=_stringify(row[10]),
                    createdAt=datetime.fromisoformat(_stringify(row[11])),
                )
            )
        return out


def transaction_to_row(tx: Transaction) -> list[object]:
    return [
        tx.id,
        tx.occurred_at.isoformat(),
        tx.type,
        tx.amount,
        tx.currency,
        tx.jar_code,
        tx.goal_name,
        tx.account,
        tx.is_fixed,
        tx.note,
        tx.source,
        tx.status,
        tx.created_at.isoformat(),
        tx.updated_at.isoformat(),
    ]


def transaction_from_row(row: list[object]) -> Transaction:
    if len(row) < 14:
        raise ValueError(f"transaction row has {len(row)} columns, expected at least 14")
    return Transaction(
        id=_stringify(row[0]),
        occurredAt=datetime.fromisoformat(_stringify(row[1])),
        type=_stringify(row[2]),
        amount=int(_stringify(row[3])),
        currency=_stringify(row[4]),
        jarCode=_stringify(row[5]),
        goalName=_stringify(row[6]),
        accountName=_stringify(row[7]),
        isFixed=_stringify(row[8]).lower() == "true",
        note=_stringify(row[9]),
        source=_stringify(row[10]),
        status=_stringify(row[11]),
        createdAt=datetime.fromisoformat(_stringify(row[12])),
        updatedAt=datetime.fromisoformat(_stringify(row[13])),
    )


def parsed_receipt_from_row(row: list[object]) -> ParsedReceipt:
    if len(row) < 11:
        raise ValueError(f"parsed receipt row has {len(row)} columns, expected at least 11")
    raw_json = _stringify(row[6])
    try:
        if raw_json and not isinstance(row[6], str):
            raw_json = json.dumps(row[6])
    except TypeError:
        raw_json = _stringify(row[6])
    return ParsedReceipt(
        id=_stringify(row[0]),
        transactionId=_stringify(row[1]),
        rawInput=_stringify(row[2]),
        regexAmount=int(_stringify(row[3]) or 0),
        regexTags=[part.strip() for part in _stringify(row[4]).split(",") if part.strip()],
        llmModel=_stringify(row[5]),
        llmOutputJson=raw_json,
        validationNote=_stringify(row[7]),
        confidence=_stringify(row[8]),
        promptSource=_stringify(row[9]),
        createdAt=datetime.fromisoformat(_stringify(row[10])),
    )

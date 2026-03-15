from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Protocol

from app.ai.client import AIClient, CompletionInput
from app.ai.json_extract import extract_json_object
from app.core.runtime import Clock
from app.domain.goals.model import Goal
from app.domain.metrics.model import Summary
from app.domain.reports.model import GenerateInput, Report, Snapshot
from app.domain.rules.model import FixedCostRule
from app.domain.transactions.model import Transaction


class ReportRepository(Protocol):
    def save(self, report: Report) -> Report: ...

    def find_by_kind_and_period(self, kind: str, period_key: str) -> Report | None: ...

    def latest_by_kind(self, kind: str) -> Report | None: ...


class MetricsReader(Protocol):
    def summary(self) -> Summary: ...


class TransactionsReader(Protocol):
    def list(self) -> list[Transaction]: ...


class GoalsReader(Protocol):
    def list(self) -> list[Goal]: ...


class RulesReader(Protocol):
    def list_fixed_cost_rules(self) -> list[FixedCostRule]: ...


class ReportsService:
    def __init__(self, repo: ReportRepository, metrics: MetricsReader, transactions: TransactionsReader, goals: GoalsReader, rules: RulesReader, ai_client: AIClient, clock: Clock, timezone_name: str, model: str, daily_prompt: str, monthly_prompt: str, daily_prompt_source: str, monthly_prompt_source: str) -> None:
        self._repo = repo
        self._metrics = metrics
        self._transactions = transactions
        self._goals = goals
        self._rules = rules
        self._ai_client = ai_client
        self._clock = clock
        self._model = model
        self._daily_prompt = daily_prompt
        self._monthly_prompt = monthly_prompt
        self._daily_prompt_source = daily_prompt_source
        self._monthly_prompt_source = monthly_prompt_source
        self._timezone_name = timezone_name

    def dashboard(self) -> Snapshot:
        now = self._clock.now().astimezone(UTC)
        daily = self._ensure("daily", now, "auto-daily")
        monthly = self._ensure("monthly", now, "auto-monthly") if now.day == 1 else self._repo.latest_by_kind("monthly")
        return Snapshot(daily=daily, monthly=monthly)

    def generate_monthly(self, input_data: GenerateInput) -> Report:
        return self._generate("monthly", self._clock.now().astimezone(UTC), input_data.trigger.strip() or "manual-monthly", force=True)

    def _ensure(self, kind: str, now: datetime, trigger: str) -> Report:
        return self._generate(kind, now, trigger, force=False)

    def _generate(self, kind: str, now: datetime, trigger: str, force: bool) -> Report:
        key = period_key(kind, now)
        if not force:
            existing = self._repo.find_by_kind_and_period(kind, key)
            if existing is not None:
                return existing
        summary = self._metrics.summary()
        txs = self._transactions.list()
        goals = self._goals.list()
        rules = self._rules.list_fixed_cost_rules()
        snapshot = build_financial_snapshot(now, txs, goals, rules, summary)
        prompt_template, prompt_source = (
            (self._monthly_prompt, self._monthly_prompt_source) if kind == "monthly" else (self._daily_prompt, self._daily_prompt_source)
        )
        prompt = render_prompt(prompt_template, kind, key, now, summary, json.dumps(snapshot, default=str, indent=2))
        try:
            output = self._ai_client.complete(CompletionInput(model=self._model, prompt=prompt))
            parsed = parse_generated_report(output.text)
            report = Report(
                id=f"RPT-{int(now.timestamp() * 1_000_000_000)}",
                kind=kind,
                periodKey=key,
                title=parsed["title"],
                summary=parsed["summary"],
                body=parsed["body"],
                verdict=parsed["verdict"],
                status=parsed["status"] or "watch",
                model=output.model or self._model or "configurable-analyst",
                promptSource=prompt_source or "default",
                trigger=trigger,
                createdAt=now,
            )
        except Exception:
            report = fallback_report(kind, key, trigger, now, prompt_source or "default", self._model or "fallback-analyst", snapshot)
        return self._repo.save(report)


def build_financial_snapshot(now: datetime, items: list[Transaction], goals: list[Goal], rules: list[FixedCostRule], summary: Summary) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "rangeLabel": now.strftime("%d %b %Y"),
        "todayExpense": 0,
        "monthExpense": 0,
        "monthIncome": 0,
        "monthTransfers": 0,
        "confirmedExpensesCount": 0,
        "draftCount": 0,
        "revertedCount": 0,
        "activeGoals": [goal.name for goal in goals if goal.status == "active"],
        "activeFixedRules": sum(1 for rule in rules if rule.is_active),
        "metrics": summary.model_dump(by_alias=True),
    }
    for item in items:
        if item.status == "reverted":
            snapshot["revertedCount"] += 1
            continue
        if item.status == "draft":
            snapshot["draftCount"] += 1
        if item.type == "OUT" and same_day(item.occurred_at, now):
            snapshot["todayExpense"] += item.amount
        if item.occurred_at.year != now.year or item.occurred_at.month != now.month:
            continue
        if item.type == "OUT":
            snapshot["monthExpense"] += item.amount
            if item.status == "confirmed":
                snapshot["confirmedExpensesCount"] += 1
        elif item.type == "IN":
            snapshot["monthIncome"] += item.amount
        elif item.type == "TRANSFER":
            snapshot["monthTransfers"] += item.amount
    return snapshot


def render_prompt(template: str, kind: str, period_key_value: str, now: datetime, summary: Summary, snapshot_json: str) -> str:
    summary_json = json.dumps(summary.model_dump(by_alias=True), indent=2)
    base = template.strip() or (
        "You are a personal finance analyst.\n"
        "Return strict JSON with keys: title, summary, body, verdict, status.\n"
        f"Kind: {kind}\nPeriod: {period_key_value}\nGenerated at: {now.isoformat()}\nMetrics:\n{{summary_json}}\nSnapshot:\n{{snapshot_json}}"
    )
    return (
        base.replace("{{kind}}", kind)
        .replace("{{period_key}}", period_key_value)
        .replace("{{generated_at}}", now.isoformat())
        .replace("{{summary_json}}", summary_json)
        .replace("{{snapshot_json}}", snapshot_json)
    )


def parse_generated_report(raw: str) -> dict[str, str]:
    payload = json.loads(extract_json_object(raw))
    if not str(payload.get("title", "")).strip() or not str(payload.get("body", "")).strip():
        raise ValueError("report output missing title or body")
    return {
        "title": str(payload.get("title", "")).strip(),
        "summary": str(payload.get("summary", "")).strip(),
        "body": str(payload.get("body", "")).strip(),
        "verdict": str(payload.get("verdict", "")).strip(),
        "status": str(payload.get("status", "")).strip(),
    }


def fallback_report(kind: str, period_key_value: str, trigger: str, now: datetime, prompt_source: str, model: str, snapshot: dict[str, object]) -> Report:
    status = snapshot["metrics"]["operatingPosture"]["status"]
    title_prefix = "Monthly" if kind == "monthly" else "Daily"
    range_label = now.strftime("%B %Y") if kind == "monthly" else now.strftime("%d %b %Y")
    return Report(
        id=f"RPT-{int(now.timestamp() * 1_000_000_000)}",
        kind=kind,
        periodKey=period_key_value,
        title=f"{title_prefix} financial status",
        summary=f"{title_prefix} report for {range_label}: STS {snapshot['metrics']['sts']['value']}, anomaly {snapshot['metrics']['anomaly']['value']}, goal pace {snapshot['metrics']['goalPace']['value']}.",
        body="\n".join(
            [
                f"Today spend: {compact_currency(snapshot['todayExpense'])}",
                f"Month expense: {compact_currency(snapshot['monthExpense'])}",
                f"Month income: {compact_currency(snapshot['monthIncome'])}",
                f"Transfers to goals: {compact_currency(snapshot['monthTransfers'])}",
                f"Draft entries waiting review: {snapshot['draftCount']}",
                f"Active goals: {len(snapshot['activeGoals'])}",
            ]
        ),
        verdict=verdict_from_status(status),
        status=status or "watch",
        model=model or "fallback-analyst",
        promptSource=prompt_source,
        trigger=trigger,
        createdAt=now,
    )


def period_key(kind: str, now: datetime) -> str:
    return now.strftime("%Y-%m") if kind == "monthly" else now.strftime("%Y-%m-%d")


def verdict_from_status(status: str) -> str:
    if status == "healthy":
        return "Financial posture looks good and under control."
    if status == "critical":
        return "Financial posture needs attention right now."
    return "Financial posture is mixed and worth monitoring."


def compact_currency(amount: int) -> str:
    sign = "-" if amount < 0 else ""
    value = abs(amount)
    if value >= 1_000_000_000:
        return f"{sign}{value / 1_000_000_000:.1f}B VND"
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.1f}M VND"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.0f}k VND"
    return f"{sign}{value} VND"


def same_day(a: datetime, b: datetime) -> bool:
    return a.astimezone(UTC).date() == b.astimezone(UTC).date()

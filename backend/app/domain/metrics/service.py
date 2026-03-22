from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.core.runtime import Clock
from app.domain.goals.model import Goal
from app.domain.metrics.model import BaselineSeries, MetricValue, OperatingPosture, Summary, SummaryItem
from app.domain.rules.model import FixedCostRule
from app.domain.transactions.model import Transaction


class TransactionsReader(Protocol):
    def list(self) -> list[Transaction]: ...


class GoalsReader(Protocol):
    def list(self) -> list[Goal]: ...


class RulesReader(Protocol):
    def list_fixed_cost_rules(self) -> list[FixedCostRule]: ...


class MetricsService:
    def __init__(self, transactions: TransactionsReader, goals: GoalsReader, rules: RulesReader, clock: Clock) -> None:
        self._transactions = transactions
        self._goals = goals
        self._rules = rules
        self._clock = clock

    def summary(self) -> Summary:
        all_transactions = self._transactions.list()
        all_goals = self._goals.list()
        all_rules = self._rules.list_fixed_cost_rules()
        now = self._clock.now().astimezone(UTC)

        sts = calculate_sts(all_transactions, now)
        anomaly = calculate_anomaly(all_transactions, now)
        tar = calculate_tar(all_transactions, now)
        goal_pace, goal_velocity, goal_eta = calculate_goal_pace(all_transactions, all_goals, now)
        fixed_cost_load, runway_months = calculate_operating_metrics(all_transactions, all_rules, now)
        return Summary(
            sts=sts,
            anomaly=anomaly,
            tar=tar,
            goalPace=goal_pace,
            operatingPosture=OperatingPosture(
                status=posture_status(sts.progress, fixed_cost_load),
                items=[
                    SummaryItem(label="Runway", value=f"{runway_months:.1f} months"),
                    SummaryItem(label="Fixed-cost load", value=f"{fixed_cost_load}%"),
                    SummaryItem(label="Goal velocity", value=goal_velocity),
                    SummaryItem(label="ETA", value=goal_eta),
                ],
            ),
            baselines=build_baselines(all_transactions, all_goals, all_rules, now),
        )


def calculate_sts(items: list[Transaction], now: datetime) -> MetricValue:
    monthly_variable_budget = 9_300_000.0
    current_month_spent = sum(
        item.amount
        for item in items
        if item.status != "reverted" and item.type == "OUT" and not item.is_fixed and item.occurred_at.year == now.year and item.occurred_at.month == now.month
    )
    days_in_month = (datetime(now.year, now.month % 12 + 1, 1, tzinfo=UTC) - timedelta(days=1)).day if now.month != 12 else 31
    remaining_days = max(1, days_in_month - now.day + 1)
    sts_value = max(0.0, (monthly_variable_budget - current_month_spent) / remaining_days)
    progress = min(100, max(0, round((sts_value / (monthly_variable_budget / days_in_month)) * 100)))
    return MetricValue(
        label="STS Today",
        value=compact_currency(int(sts_value)),
        caption="Daily spend allowance based on remaining monthly variable budget.",
        progress=int(progress),
        status=status_from_progress(int(progress)),
    )


def calculate_anomaly(items: list[Transaction], now: datetime) -> MetricValue:
    today_spend = 0.0
    history: list[float] = []
    for item in items:
        if item.status == "reverted" or item.type != "OUT" or item.is_fixed:
            continue
        if same_day(item.occurred_at, now):
            today_spend += item.amount
        if item.occurred_at < now and item.occurred_at > now - timedelta(days=30):
            history.append(float(item.amount))
    mean = average(history)
    stddev = standard_deviation(history, mean)
    z_score = 0.0 if stddev == 0 else (today_spend - mean) / stddev
    progress = min(100, max(0, round((abs(z_score) / 2.5) * 100)))
    return MetricValue(
        label="Anomaly Score",
        value=f"{z_score:.2f}",
        caption="Variable-spend pacing versus your recent baseline.",
        progress=int(progress),
        status=anomaly_status(z_score),
    )


def calculate_goal_pace(items: list[Transaction], goals_list: list[Goal], now: datetime) -> tuple[MetricValue, str, str]:
    if not goals_list:
        return MetricValue(label="Goal Pace", value="0%", caption="No active goals yet.", progress=0, status="idle"), "0/mo", "N/A"
    active_goal = goals_list[0]
    total_transferred = 0
    recent_transferred = 0
    for item in items:
        if item.status == "reverted" or item.type != "TRANSFER" or item.goal_name != active_goal.name:
            continue
        total_transferred += item.amount
        if item.occurred_at > now - timedelta(days=90):
            recent_transferred += item.amount
    progress = 0
    if active_goal.target_amount > 0:
        progress = min(100, max(0, round((total_transferred / active_goal.target_amount) * 100)))
    monthly_velocity = recent_transferred / 3.0
    eta = "N/A"
    if monthly_velocity > 0 and active_goal.target_amount > total_transferred:
        months_remaining = math.ceil((active_goal.target_amount - total_transferred) / monthly_velocity)
        eta_dt = now.replace(day=1) + timedelta(days=32 * months_remaining)
        eta = eta_dt.strftime("%b %Y")
    return (
        MetricValue(
            label="Goal Pace",
            value=f"{int(progress)}%",
            caption="Current savings velocity relative to target timeline.",
            progress=int(progress),
            status=status_from_progress(int(progress)),
        ),
        compact_currency(int(monthly_velocity)) + "/mo",
        eta,
    )


def calculate_tar(items: list[Transaction], now: datetime) -> MetricValue:
    month_income = 0
    month_variable_out = 0
    month_fixed_out = 0
    month_goal_transfers = 0

    for item in items:
        if item.status == "reverted" or item.occurred_at.year != now.year or item.occurred_at.month != now.month:
            continue
        if item.type == "IN":
            month_income += item.amount
        elif item.type == "OUT":
            if item.is_fixed:
                month_fixed_out += item.amount
            else:
                month_variable_out += item.amount
        elif item.type == "TRANSFER":
            month_goal_transfers += item.amount

    if month_income <= 0:
        return MetricValue(
            label="TAR",
            value="0%",
            caption="True accumulation rate based on income kept after spending and transfers.",
            progress=0,
            status="idle",
        )

    retained = month_income - month_variable_out - month_fixed_out + month_goal_transfers
    ratio = retained / month_income
    progress = min(100, max(0, round(ratio * 100)))
    return MetricValue(
        label="TAR",
        value=f"{int(round(ratio * 100))}%",
        caption="True accumulation rate based on income kept after spending and transfers.",
        progress=int(progress),
        status=status_from_progress(int(progress)),
    )


def calculate_operating_metrics(items: list[Transaction], rules_list: list[FixedCostRule], now: datetime) -> tuple[int, float]:
    fixed_spent = 0.0
    income = 0.0
    liquid = 0.0
    for item in items:
        if item.status == "reverted":
            continue
        if item.type == "OUT" and item.is_fixed and item.occurred_at.year == now.year and item.occurred_at.month == now.month:
            fixed_spent += item.amount
        if item.type == "IN" and item.occurred_at > now - timedelta(days=90):
            income += item.amount
            liquid += item.amount * 0.3
    if fixed_spent == 0:
        fixed_spent = sum(rule.expected_amount for rule in rules_list if rule.is_active)
    avg_monthly_income = income / 3 if income else 0
    fixed_cost_load = int(round((fixed_spent / avg_monthly_income) * 100)) if avg_monthly_income > 0 else 0
    runway_months = liquid / fixed_spent if fixed_spent > 0 else 0.0
    return fixed_cost_load, runway_months


def build_baselines(items: list[Transaction], goals_list: list[Goal], rules_list: list[FixedCostRule], now: datetime) -> list[BaselineSeries]:
    variable_series: list[int] = []
    fixed_series: list[int] = []
    goal_series: list[int] = []
    for month_offset in range(11, -1, -1):
        month_time = datetime(now.year, now.month, 1, tzinfo=UTC)
        month_shift = month_time.month - month_offset
        year = month_time.year + (month_shift - 1) // 12
        month = ((month_shift - 1) % 12) + 1
        shifted = datetime(year, month, 1, tzinfo=UTC)
        variable_series.append(int(monthly_variable_spend(items, shifted)))
        fixed_series.append(int(monthly_fixed_spend(items, rules_list, shifted, now)))
        goal_series.append(int(monthly_goal_transfers(items, goals_list, shifted)))
    return [
        BaselineSeries(label="Variable spend", description="Rolling monthly pace for variable expenses.", values=normalize_series(variable_series), current=compact_currency(variable_series[-1]), delta=series_delta(variable_series), colorToken="var(--tp-danger)"),
        BaselineSeries(label="Fixed-cost load", description="Monthly fixed obligations against current operating structure.", values=normalize_series(fixed_series), current=compact_currency(fixed_series[-1]), delta=series_delta(fixed_series), colorToken="var(--tp-accent)"),
        BaselineSeries(label="Goal velocity", description="Monthly transfer momentum toward active goals.", values=normalize_series(goal_series), current=compact_currency(goal_series[-1]), delta=series_delta(goal_series), colorToken="var(--tp-danger-soft)"),
    ]


def monthly_variable_spend(items: list[Transaction], month: datetime) -> float:
    return float(sum(item.amount for item in items if item.status != "reverted" and item.type == "OUT" and not item.is_fixed and item.occurred_at.year == month.year and item.occurred_at.month == month.month))


def monthly_fixed_spend(items: list[Transaction], rules_list: list[FixedCostRule], month: datetime, now: datetime) -> float:
    total = float(sum(item.amount for item in items if item.status != "reverted" and item.type == "OUT" and item.is_fixed and item.occurred_at.year == month.year and item.occurred_at.month == month.month))
    if total == 0 and month.year == now.year and month.month == now.month:
        total = float(sum(rule.expected_amount for rule in rules_list if rule.is_active))
    return total


def monthly_goal_transfers(items: list[Transaction], goals_list: list[Goal], month: datetime) -> float:
    if not goals_list:
        return 0.0
    return float(sum(item.amount for item in items if item.status != "reverted" and item.type == "TRANSFER" and item.occurred_at.year == month.year and item.occurred_at.month == month.month))


def normalize_series(values: list[int]) -> list[int]:
    if not values:
        return values
    min_v, max_v = min(values), max(values)
    if max_v == min_v:
        return [50 for _ in values]
    return [round(((value - min_v) / (max_v - min_v)) * 100) for value in values]


def series_delta(values: list[int]) -> str:
    if len(values) < 2 or values[-2] == 0:
        return "0% vs previous"
    delta = ((values[-1] - values[-2]) / values[-2]) * 100
    return f"{delta:+.0f}% vs previous"


def compact_currency(value: int) -> str:
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}m"
    if value >= 1_000:
        return f"{value/1_000:.0f}k"
    return str(value)


def status_from_progress(progress: int) -> str:
    if progress >= 80:
        return "healthy"
    if progress >= 50:
        return "warning"
    return "critical"


def anomaly_status(z: float) -> str:
    if abs(z) > 1.96:
        return "critical"
    if abs(z) > 1.0:
        return "warning"
    return "healthy"


def posture_status(sts_progress: int, fixed_cost_load: int) -> str:
    if sts_progress < 40 or fixed_cost_load > 60:
        return "High alert"
    if sts_progress < 70 or fixed_cost_load > 40:
        return "Moderate risk"
    return "Stable"


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def standard_deviation(values: list[float], mean: float) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def same_day(a: datetime, b: datetime) -> bool:
    return a.year == b.year and a.month == b.month and a.day == b.day

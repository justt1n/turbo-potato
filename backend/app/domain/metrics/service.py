from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.core.runtime import Clock
from app.domain.goals.model import Goal
from app.domain.metrics.model import BaselineSeries, MetricValue, OperatingPosture, Summary, SummaryItem
from app.domain.rules.model import FixedCostRule
from app.domain.sources.model import Source
from app.domain.transactions.model import Transaction


class TransactionsReader(Protocol):
    def list(self) -> list[Transaction]: ...


class GoalsReader(Protocol):
    def list(self) -> list[Goal]: ...


class RulesReader(Protocol):
    def list_fixed_cost_rules(self) -> list[FixedCostRule]: ...


class SourcesReader(Protocol):
    def list(self) -> list[Source]: ...


class MetricsService:
    def __init__(
        self,
        transactions: TransactionsReader,
        goals: GoalsReader,
        rules: RulesReader,
        sources: SourcesReader,
        clock: Clock,
    ) -> None:
        self._transactions = transactions
        self._goals = goals
        self._rules = rules
        self._sources = sources
        self._clock = clock

    def summary(self) -> Summary:
        all_transactions = self._transactions.list()
        all_goals = self._goals.list()
        all_rules = self._rules.list_fixed_cost_rules()
        all_sources = self._sources.list()
        now = self._clock.now().astimezone(UTC)

        sts = calculate_sts(all_transactions, all_goals, all_rules, now)
        anomaly = calculate_anomaly(all_transactions, now)
        tar = calculate_tar(all_transactions, now)
        goal_pace, goal_velocity, goal_eta = calculate_goal_pace(all_transactions, all_goals, now)
        fixed_cost_load, runway_months = calculate_operating_metrics(all_transactions, all_rules, all_sources, now)
        return Summary(
            sts=sts,
            anomaly=anomaly,
            tar=tar,
            goalPace=goal_pace,
            operatingPosture=OperatingPosture(
                status=posture_status(sts.progress, fixed_cost_load, runway_months),
                items=[
                    SummaryItem(label="Runway", value=f"{runway_months:.1f} months"),
                    SummaryItem(label="Fixed-cost load", value=f"{fixed_cost_load}%"),
                    SummaryItem(label="Goal velocity", value=goal_velocity),
                    SummaryItem(label="ETA", value=goal_eta),
                ],
            ),
            baselines=build_baselines(all_transactions, all_goals, all_rules, now),
        )


def calculate_sts(items: list[Transaction], goals_list: list[Goal], rules_list: list[FixedCostRule], now: datetime) -> MetricValue:
    income_baseline = baseline_monthly_income(items, now)
    fixed_commitment = month_fixed_commitment(items, rules_list, now)
    goal_commitment = required_goal_commitment(goals_list, items, now)
    current_month_spent = sum(
        item.amount
        for item in items
        if item.status != "reverted"
        and item.type == "OUT"
        and not item.is_fixed
        and item.occurred_at.year == now.year
        and item.occurred_at.month == now.month
    )
    days_in_month = (datetime(now.year, now.month % 12 + 1, 1, tzinfo=UTC) - timedelta(days=1)).day if now.month != 12 else 31
    remaining_days = max(1, days_in_month - now.day + 1)
    flexible_budget = max(0.0, income_baseline - fixed_commitment - goal_commitment)
    sts_value = max(0.0, (flexible_budget - current_month_spent) / remaining_days)
    target_daily_allowance = flexible_budget / days_in_month if days_in_month > 0 else 0.0
    progress = min(100, max(0, round((sts_value / target_daily_allowance) * 100))) if target_daily_allowance > 0 else 0
    return MetricValue(
        label="STS",
        value=compact_currency(int(sts_value)),
        caption="Safe-to-spend per day after fixed commitments and target funding needs.",
        progress=int(progress),
        status=status_from_progress(int(progress)),
    )


def calculate_anomaly(items: list[Transaction], now: datetime) -> MetricValue:
    today_spend = 0.0
    daily_totals: dict[str, float] = {}

    for day_offset in range(60, -1, -1):
        day = (now - timedelta(days=day_offset)).date().isoformat()
        daily_totals[day] = 0.0

    for item in items:
        if item.status == "reverted" or item.type != "OUT" or item.is_fixed:
            continue
        day_key = item.occurred_at.astimezone(UTC).date().isoformat()
        if day_key in daily_totals:
            daily_totals[day_key] += float(item.amount)
        if same_day(item.occurred_at, now):
            today_spend += item.amount

    today_key = now.date().isoformat()
    history = [value for day, value in daily_totals.items() if day != today_key]
    median_value = median(history)
    mad = median([abs(value - median_value) for value in history])
    z_score = 0.0 if mad == 0 else 0.6745 * (today_spend - median_value) / mad
    progress = min(100, max(0, round((abs(z_score) / 3.5) * 100)))
    return MetricValue(
        label="Anomaly",
        value=f"{z_score:.2f}",
        caption="Robust daily-spend anomaly score versus the last 60 days.",
        progress=int(progress),
        status=anomaly_status(z_score),
    )


def calculate_goal_pace(items: list[Transaction], goals_list: list[Goal], now: datetime) -> tuple[MetricValue, str, str]:
    active_goals = [goal for goal in goals_list if goal.status == "active"]
    if not active_goals:
        return MetricValue(label="Goal Pace", value="0%", caption="No active goals yet.", progress=0, status="idle"), "0/mo", "N/A"
    active_goal = sorted(active_goals, key=lambda goal: (goal.target_date or datetime.max.replace(tzinfo=UTC), goal.start_date))[0]
    total_transferred = 0.0
    recent_transferred = 0.0
    for item in items:
        if item.status == "reverted" or item.type != "TRANSFER" or item.goal_name != active_goal.name:
            continue
        total_transferred += item.amount
        if item.occurred_at > now - timedelta(days=90):
            recent_transferred += item.amount
    monthly_velocity = recent_transferred / 3.0
    remaining = max(0.0, active_goal.target_amount - total_transferred)
    pace_ratio = 0.0
    if active_goal.target_date and active_goal.target_date > now and remaining > 0:
        months_remaining = max(1, month_span(now, active_goal.target_date))
        required_monthly = remaining / months_remaining
        pace_ratio = monthly_velocity / required_monthly if required_monthly > 0 else 1.0
    elif active_goal.target_amount > 0:
        pace_ratio = total_transferred / active_goal.target_amount
    progress = min(100, max(0, round(pace_ratio * 100)))
    monthly_velocity = recent_transferred / 3.0
    eta = "N/A"
    if monthly_velocity > 0 and remaining > 0:
        months_remaining = math.ceil(remaining / monthly_velocity)
        eta_dt = now.replace(day=1) + timedelta(days=32 * months_remaining)
        eta = eta_dt.strftime("%b %Y")
    return (
        MetricValue(
            label="Goal Pace",
            value=f"{int(round(pace_ratio * 100))}%",
            caption="Current goal funding pace versus the rate required to hit target.",
            progress=int(progress),
            status=goal_pace_status(pace_ratio),
        ),
        compact_currency(int(monthly_velocity)) + "/mo",
        eta,
    )


def calculate_tar(items: list[Transaction], now: datetime) -> MetricValue:
    month_income = 0
    month_variable_out = 0
    month_fixed_out = 0

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
    if month_income <= 0:
        return MetricValue(
            label="TAR",
            value="0%",
            caption="Net savings rate based on income kept after actual spending.",
            progress=0,
            status="idle",
        )

    retained = month_income - month_variable_out - month_fixed_out
    ratio = retained / month_income
    progress = min(100, max(0, round(ratio * 100)))
    return MetricValue(
        label="TAR",
        value=f"{int(round(ratio * 100))}%",
        caption="Net savings rate after actual consumption; transfers are not double-counted.",
        progress=int(progress),
        status=savings_rate_status(ratio),
    )


def calculate_operating_metrics(
    items: list[Transaction],
    rules_list: list[FixedCostRule],
    sources: list[Source],
    now: datetime,
) -> tuple[int, float]:
    fixed_spent = month_fixed_commitment(items, rules_list, now)
    avg_monthly_income = baseline_monthly_income(items, now)
    liquid = liquid_reserves(sources)
    variable_burn = baseline_monthly_variable_spend(items, now)
    fixed_cost_load = int(round((fixed_spent / avg_monthly_income) * 100)) if avg_monthly_income > 0 else 0
    monthly_burn = fixed_spent + variable_burn
    runway_months = liquid / monthly_burn if monthly_burn > 0 else 0.0
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


def posture_status(sts_progress: int, fixed_cost_load: int, runway_months: float) -> str:
    if sts_progress < 45 or fixed_cost_load > 60 or runway_months < 3:
        return "High alert"
    if sts_progress < 70 or fixed_cost_load > 40 or runway_months < 6:
        return "Moderate risk"
    return "Stable"


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def same_day(a: datetime, b: datetime) -> bool:
    return a.year == b.year and a.month == b.month and a.day == b.day


def month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1, tzinfo=UTC)


def shift_month(anchor: datetime, offset: int) -> datetime:
    month_index = anchor.month + offset
    year = anchor.year + (month_index - 1) // 12
    month = ((month_index - 1) % 12) + 1
    return datetime(year, month, 1, tzinfo=UTC)


def monthly_income(items: list[Transaction], month: datetime) -> float:
    return float(
        sum(
            item.amount
            for item in items
            if item.status != "reverted" and item.type == "IN" and item.occurred_at.year == month.year and item.occurred_at.month == month.month
        )
    )


def baseline_monthly_income(items: list[Transaction], now: datetime) -> float:
    anchor = month_start(now)
    history = [monthly_income(items, shift_month(anchor, offset)) for offset in (-3, -2, -1)]
    realized = [value for value in history if value > 0]
    if realized:
        return average(realized)
    return monthly_income(items, anchor)


def baseline_monthly_variable_spend(items: list[Transaction], now: datetime) -> float:
    anchor = month_start(now)
    history = [monthly_variable_spend(items, shift_month(anchor, offset)) for offset in (-3, -2, -1)]
    realized = [value for value in history if value > 0]
    if realized:
        return average(realized)
    return monthly_variable_spend(items, anchor)


def month_fixed_commitment(items: list[Transaction], rules_list: list[FixedCostRule], now: datetime) -> float:
    fixed_spent = float(
        sum(
            item.amount
            for item in items
            if item.status != "reverted"
            and item.type == "OUT"
            and item.is_fixed
            and item.occurred_at.year == now.year
            and item.occurred_at.month == now.month
        )
    )
    expected_rules = float(sum(rule.expected_amount for rule in rules_list if rule.is_active))
    return max(fixed_spent, expected_rules)


def total_goal_funded(goal: Goal, items: list[Transaction]) -> float:
    return float(
        sum(
            item.amount
            for item in items
            if item.status != "reverted" and item.type == "TRANSFER" and item.goal_name == goal.name
        )
    )


def required_goal_commitment(goals_list: list[Goal], items: list[Transaction], now: datetime) -> float:
    total = 0.0
    for goal in goals_list:
        if goal.status != "active":
            continue
        funded = total_goal_funded(goal, items)
        remaining = max(0.0, goal.target_amount - funded)
        if remaining <= 0:
            continue
        if goal.target_date and goal.target_date > now:
            months_remaining = max(1, month_span(now, goal.target_date))
            total += remaining / months_remaining
    return total


def month_span(start: datetime, end: datetime) -> int:
    return max(1, (end.year - start.year) * 12 + (end.month - start.month) + (1 if end.day >= start.day else 0))


def goal_pace_status(pace_ratio: float) -> str:
    if pace_ratio >= 1.0:
        return "healthy"
    if pace_ratio >= 0.75:
        return "warning"
    return "critical"


def savings_rate_status(ratio: float) -> str:
    if ratio >= 0.2:
        return "healthy"
    if ratio >= 0.1:
        return "warning"
    return "critical"


def liquid_reserves(sources: list[Source]) -> float:
    reserves = 0.0
    for source in sources:
        if not source.is_active:
            continue
        if source.kind == "gold":
            reserves += source.gold_quantity_chi * source.gold_price_per_chi * 0.85
            continue
        reserves += max(0, source.actual_balance)
    return reserves

from __future__ import annotations

from typing import Protocol

from app.domain.rules.model import CreateFixedCostRuleInput, FixedCostRule, UpdateFixedCostRuleInput


class RulesRepository(Protocol):
    def create_fixed_cost_rule(self, rule: FixedCostRule) -> FixedCostRule: ...

    def update_fixed_cost_rule(self, current_name: str, rule: FixedCostRule) -> FixedCostRule: ...

    def list_fixed_cost_rules(self) -> list[FixedCostRule]: ...


class RulesService:
    def __init__(self, repo: RulesRepository) -> None:
        self._repo = repo

    def create_fixed_cost_rule(self, input_data: CreateFixedCostRuleInput) -> FixedCostRule:
        name = input_data.name.strip()
        if not name:
            raise ValueError("name is required")
        if input_data.expected_amount <= 0:
            raise ValueError("expectedAmount must be greater than zero")
        if input_data.window_start_day < 1 or input_data.window_start_day > 31:
            raise ValueError("windowStartDay must be between 1 and 31")
        if input_data.window_end_day < input_data.window_start_day or input_data.window_end_day > 31:
            raise ValueError("windowEndDay must be between windowStartDay and 31")

        rule = FixedCostRule(
            name=name,
            expectedAmount=input_data.expected_amount,
            windowStartDay=input_data.window_start_day,
            windowEndDay=input_data.window_end_day,
            linkedJarCode=input_data.linked_jar_code.strip(),
            isActive=input_data.is_active,
        )
        return self._repo.create_fixed_cost_rule(rule)

    def list_fixed_cost_rules(self) -> list[FixedCostRule]:
        return self._repo.list_fixed_cost_rules()

    def update_fixed_cost_rule(self, current_name: str, input_data: UpdateFixedCostRuleInput) -> FixedCostRule:
        name = current_name.strip()
        if not name:
            raise ValueError("rule name is required")
        if input_data.expected_amount <= 0:
            raise ValueError("expectedAmount must be greater than zero")
        if input_data.window_start_day < 1 or input_data.window_start_day > 31:
            raise ValueError("windowStartDay must be between 1 and 31")
        if input_data.window_end_day < input_data.window_start_day or input_data.window_end_day > 31:
            raise ValueError("windowEndDay must be between windowStartDay and 31")

        rule = FixedCostRule(
            name=name,
            expectedAmount=input_data.expected_amount,
            windowStartDay=input_data.window_start_day,
            windowEndDay=input_data.window_end_day,
            linkedJarCode=input_data.linked_jar_code.strip(),
            isActive=input_data.is_active,
        )
        return self._repo.update_fixed_cost_rule(name, rule)

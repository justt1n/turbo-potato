from __future__ import annotations

from typing import Protocol

from app.core.runtime import Clock
from app.domain.goals.model import CreateInput, Goal, UpdateInput


class GoalRepository(Protocol):
    def create_goal(self, goal: Goal) -> Goal: ...

    def update_goal(self, current_name: str, goal: Goal) -> Goal: ...

    def list_goals(self) -> list[Goal]: ...


class GoalService:
    def __init__(self, repo: GoalRepository, clock: Clock) -> None:
        self._repo = repo
        self._clock = clock

    def create(self, input_data: CreateInput) -> Goal:
        name = input_data.name.strip()
        if not name:
            raise ValueError("name is required")
        if input_data.target_amount <= 0:
            raise ValueError("targetAmount must be greater than zero")

        goal = Goal(
            name=name,
            targetAmount=input_data.target_amount,
            startDate=input_data.start_date or self._clock.now(),
            targetDate=input_data.target_date,
            status=input_data.status or "active",
        )
        return self._repo.create_goal(goal)

    def list(self) -> list[Goal]:
        return self._repo.list_goals()

    def update(self, current_name: str, input_data: UpdateInput) -> Goal:
        name = current_name.strip()
        if not name:
            raise ValueError("goal name is required")
        if input_data.target_amount <= 0:
            raise ValueError("targetAmount must be greater than zero")

        goal = Goal(
            name=name,
            targetAmount=input_data.target_amount,
            startDate=input_data.start_date or self._clock.now(),
            targetDate=input_data.target_date,
            status=input_data.status,
        )
        return self._repo.update_goal(name, goal)

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GoalStatus = Literal["active", "completed", "paused"]


class Goal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    target_amount: int = Field(alias="targetAmount")
    start_date: datetime = Field(alias="startDate")
    target_date: datetime | None = Field(default=None, alias="targetDate")
    status: GoalStatus


class CreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    target_amount: int = Field(alias="targetAmount")
    start_date: datetime | None = Field(default=None, alias="startDate")
    target_date: datetime | None = Field(default=None, alias="targetDate")
    status: GoalStatus | None = None

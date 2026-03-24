from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FixedCostRule(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    expected_amount: int = Field(alias="expectedAmount")
    window_start_day: int = Field(alias="windowStartDay")
    window_end_day: int = Field(alias="windowEndDay")
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    is_active: bool = Field(alias="isActive")


class CreateFixedCostRuleInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    expected_amount: int = Field(alias="expectedAmount")
    window_start_day: int = Field(alias="windowStartDay")
    window_end_day: int = Field(alias="windowEndDay")
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    is_active: bool = Field(alias="isActive")


class UpdateFixedCostRuleInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    expected_amount: int = Field(alias="expectedAmount")
    window_start_day: int = Field(alias="windowStartDay")
    window_end_day: int = Field(alias="windowEndDay")
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    is_active: bool = Field(alias="isActive")

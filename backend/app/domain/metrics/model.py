from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MetricValue(BaseModel):
    label: str
    value: str
    caption: str
    progress: int
    status: str


class SummaryItem(BaseModel):
    label: str
    value: str


class OperatingPosture(BaseModel):
    status: str
    items: list[SummaryItem]


class BaselineSeries(BaseModel):
    label: str
    description: str
    values: list[int]
    current: str
    delta: str
    color_token: str = Field(alias="colorToken")


class Summary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sts: MetricValue
    anomaly: MetricValue
    tar: MetricValue
    goal_pace: MetricValue = Field(alias="goalPace")
    operating_posture: OperatingPosture = Field(alias="operatingPosture")
    baselines: list[BaselineSeries]

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReportKind = Literal["daily", "monthly"]


class Report(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    kind: ReportKind
    period_key: str = Field(alias="periodKey")
    title: str
    summary: str
    body: str
    verdict: str
    status: str
    model: str
    prompt_source: str = Field(alias="promptSource")
    trigger: str
    created_at: datetime = Field(alias="createdAt")


class Snapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    daily: Report
    monthly: Report | None = None


class GenerateInput(BaseModel):
    trigger: str = ""
    actor: str = ""

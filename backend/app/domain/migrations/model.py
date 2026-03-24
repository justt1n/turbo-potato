from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MigrateLegacyJarsInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dry_run: bool = Field(default=False, alias="dryRun")


class MigrationItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    jar_code: str = Field(alias="jarCode")
    jar_name: str = Field(alias="jarName")
    source_code: str = Field(alias="sourceCode")
    status: str
    reason: str


class MigrationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dry_run: bool = Field(alias="dryRun")
    candidates: int
    created: int
    skipped: int
    items: list[MigrationItem]

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AssetItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    name: str
    kind: str
    provider: str = ""
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    opening_balance: int = Field(alias="openingBalance")
    inflow_total: int = Field(alias="inflowTotal")
    outflow_total: int = Field(alias="outflowTotal")
    book_balance: int = Field(alias="bookBalance")
    actual_balance: int = Field(alias="actualBalance")
    gold_quantity_chi: float = Field(default=0, alias="goldQuantityChi")
    gold_price_per_chi: int = Field(default=0, alias="goldPricePerChi")
    discrepancy: int
    is_active: bool = Field(alias="isActive")
    note: str = ""
    last_activity_at: str | None = Field(default=None, alias="lastActivityAt")


class JarTotal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    jar_code: str = Field(alias="jarCode")
    total_book_balance: int = Field(alias="totalBookBalance")
    total_actual_balance: int = Field(alias="totalActualBalance")
    source_count: int = Field(alias="sourceCount")


class AssetOverview(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_book_balance: int = Field(alias="totalBookBalance")
    total_actual_balance: int = Field(alias="totalActualBalance")
    total_discrepancy: int = Field(alias="totalDiscrepancy")
    active_sources: int = Field(alias="activeSources")
    jar_totals: list[JarTotal] = Field(alias="jarTotals")
    items: list[AssetItem]

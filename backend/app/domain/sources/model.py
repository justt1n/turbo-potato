from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    name: str
    kind: str = "wallet"
    provider: str = ""
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    opening_balance: int = Field(default=0, alias="openingBalance")
    actual_balance: int = Field(default=0, alias="actualBalance")
    gold_quantity_chi: float = Field(default=0, alias="goldQuantityChi")
    gold_price_per_chi: int = Field(default=0, alias="goldPricePerChi")
    is_active: bool = Field(default=True, alias="isActive")
    note: str = ""


class CreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    name: str
    kind: str = "wallet"
    provider: str = ""
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    opening_balance: int = Field(default=0, alias="openingBalance")
    actual_balance: int | None = Field(default=None, alias="actualBalance")
    gold_quantity_chi: float = Field(default=0, alias="goldQuantityChi")
    gold_price_per_chi: int = Field(default=0, alias="goldPricePerChi")
    is_active: bool = Field(default=True, alias="isActive")
    note: str = ""


class UpdateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    kind: str = "wallet"
    provider: str = ""
    linked_jar_code: str = Field(default="", alias="linkedJarCode")
    opening_balance: int = Field(default=0, alias="openingBalance")
    actual_balance: int = Field(default=0, alias="actualBalance")
    gold_quantity_chi: float = Field(default=0, alias="goldQuantityChi")
    gold_price_per_chi: int = Field(default=0, alias="goldPricePerChi")
    is_active: bool = Field(default=True, alias="isActive")
    note: str = ""

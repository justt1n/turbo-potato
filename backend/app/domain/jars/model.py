from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Jar(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    name: str
    kind: str = "cash"
    opening_balance: int = Field(default=0, alias="openingBalance")
    actual_balance: int = Field(default=0, alias="actualBalance")
    is_active: bool = Field(default=True, alias="isActive")
    note: str = ""


class CreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    name: str
    kind: str = "cash"
    opening_balance: int = Field(default=0, alias="openingBalance")
    actual_balance: int | None = Field(default=None, alias="actualBalance")
    is_active: bool = Field(default=True, alias="isActive")
    note: str = ""


class UpdateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    kind: str = "cash"
    opening_balance: int = Field(default=0, alias="openingBalance")
    actual_balance: int = Field(default=0, alias="actualBalance")
    is_active: bool = Field(default=True, alias="isActive")
    note: str = ""

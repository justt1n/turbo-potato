from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransactionType = Literal["IN", "OUT", "TRANSFER"]
TransactionStatus = Literal["draft", "confirmed", "reverted"]


class Transaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    occurred_at: datetime = Field(alias="occurredAt")
    type: TransactionType
    amount: int
    currency: str
    jar_code: str = Field(default="", alias="jarCode")
    goal_name: str = Field(default="", alias="goalName")
    account: str = Field(default="", alias="accountName")
    is_fixed: bool = Field(default=False, alias="isFixed")
    note: str = ""
    source: str
    status: TransactionStatus
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class CreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    occurred_at: datetime | None = Field(default=None, alias="occurredAt")
    type: TransactionType
    amount: int
    currency: str = ""
    jar_code: str = Field(default="", alias="jarCode")
    goal_name: str = Field(default="", alias="goalName")
    account: str = Field(default="", alias="accountName")
    is_fixed: bool = Field(default=False, alias="isFixed")
    note: str = ""
    source: str = ""
    status: TransactionStatus | None = None


class UpdateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    occurred_at: datetime = Field(alias="occurredAt")
    type: TransactionType
    amount: int
    currency: str
    jar_code: str = Field(default="", alias="jarCode")
    goal_name: str = Field(default="", alias="goalName")
    account: str = Field(default="", alias="accountName")
    is_fixed: bool = Field(default=False, alias="isFixed")
    note: str = ""
    status: TransactionStatus | None = None


class AuditEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    transaction_id: str = Field(alias="transactionId")
    action: str
    previous_value: str = Field(alias="previousValue")
    new_value: str = Field(alias="newValue")
    reason: str
    actor: str
    created_at: datetime = Field(alias="createdAt")

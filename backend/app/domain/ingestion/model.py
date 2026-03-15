from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.transactions.model import Transaction, UpdateInput


class ParsedReceipt(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    transaction_id: str = Field(alias="transactionId")
    raw_input: str = Field(alias="rawInput")
    regex_amount: int = Field(alias="regexAmount")
    regex_tags: list[str] = Field(alias="regexTags")
    llm_model: str = Field(alias="llmModel")
    llm_output_json: str = Field(alias="llmOutputJson")
    validation_note: str = Field(alias="validationNote")
    confidence: str
    prompt_source: str = Field(alias="promptSource")
    created_at: datetime = Field(alias="createdAt")


class IngestInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    raw_input: str = Field(alias="rawInput")
    source: str = ""
    actor: str = ""


class Result(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: str = Field(alias="transactionId")
    receipt: ParsedReceipt


class ParsedReceiptReviewItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    receipt: ParsedReceipt
    transaction: Transaction | None = None


class ReviewActionInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str = ""
    actor: str = ""


class ReviewCorrectInput(UpdateInput):
    model_config = ConfigDict(populate_by_name=True)

    reason: str = ""
    actor: str = ""

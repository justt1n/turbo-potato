from __future__ import annotations

from typing import Protocol

from app.domain.ingestion.model import ParsedReceipt, ParsedReceiptReviewItem, ReviewCorrectInput
from app.domain.transactions.model import Transaction, UpdateInput


class ReceiptReader(Protocol):
    def get_parsed_receipt(self, receipt_id: str) -> ParsedReceipt: ...

    def list_parsed_receipts(self) -> list[ParsedReceipt]: ...


class TransactionReader(Protocol):
    def get(self, tx_id: str) -> Transaction: ...

    def correct(self, tx_id: str, input_data: UpdateInput, reason: str, actor: str) -> Transaction: ...

    def undo(self, tx_id: str, reason: str, actor: str) -> Transaction: ...


class ParsedReceiptReviewService:
    def __init__(self, receipts: ReceiptReader, transactions: TransactionReader) -> None:
        self._receipts = receipts
        self._transactions = transactions

    def list(self) -> list[ParsedReceiptReviewItem]:
        items = self._receipts.list_parsed_receipts()
        return [self._build_item(receipt) for receipt in items]

    def get(self, receipt_id: str) -> ParsedReceiptReviewItem:
        receipt = self._receipts.get_parsed_receipt(receipt_id)
        return self._build_item(receipt)

    def _build_item(self, receipt: ParsedReceipt) -> ParsedReceiptReviewItem:
        transaction = None
        try:
            transaction = self._transactions.get(receipt.transaction_id)
        except ValueError:
            transaction = None
        return ParsedReceiptReviewItem(receipt=receipt, transaction=transaction)

    def confirm(self, receipt_id: str, reason: str, actor: str) -> ParsedReceiptReviewItem:
        receipt = self._receipts.get_parsed_receipt(receipt_id)
        current = self._transactions.get(receipt.transaction_id)
        updated = self._transactions.correct(
            receipt.transaction_id,
            UpdateInput(
                occurredAt=current.occurred_at,
                type=current.type,
                amount=current.amount,
                currency=current.currency,
                jarCode=current.jar_code,
                goalName=current.goal_name,
                accountName=current.account,
                isFixed=current.is_fixed,
                note=current.note,
                status="confirmed",
            ),
            reason.strip() or "confirmed from review",
            actor.strip(),
        )
        return ParsedReceiptReviewItem(receipt=receipt, transaction=updated)

    def correct(self, receipt_id: str, input_data: ReviewCorrectInput) -> ParsedReceiptReviewItem:
        receipt = self._receipts.get_parsed_receipt(receipt_id)
        updated = self._transactions.correct(
            receipt.transaction_id,
            UpdateInput(
                occurredAt=input_data.occurred_at,
                type=input_data.type,
                amount=input_data.amount,
                currency=input_data.currency,
                jarCode=input_data.jar_code,
                goalName=input_data.goal_name,
                accountName=input_data.account,
                isFixed=input_data.is_fixed,
                note=input_data.note,
                status=input_data.status,
            ),
            input_data.reason.strip(),
            input_data.actor.strip(),
        )
        return ParsedReceiptReviewItem(receipt=receipt, transaction=updated)

    def undo(self, receipt_id: str, reason: str, actor: str) -> ParsedReceiptReviewItem:
        receipt = self._receipts.get_parsed_receipt(receipt_id)
        updated = self._transactions.undo(
            receipt.transaction_id,
            reason.strip() or "reverted from review",
            actor.strip(),
        )
        return ParsedReceiptReviewItem(receipt=receipt, transaction=updated)

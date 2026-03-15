from __future__ import annotations

import json
from typing import Protocol

from app.core.runtime import Clock, TransactionIDGenerator
from app.domain.transactions.model import AuditEntry, CreateInput, Transaction, UpdateInput


class TransactionRepository(Protocol):
    def create_transaction(self, tx: Transaction) -> Transaction: ...

    def get_transaction(self, tx_id: str) -> Transaction: ...

    def update_transaction(self, tx: Transaction) -> Transaction: ...

    def list_transactions(self) -> list[Transaction]: ...


class AuditLogger(Protocol):
    def log(self, entry: AuditEntry) -> None: ...


class TransactionService:
    def __init__(
        self,
        repo: TransactionRepository,
        audit: AuditLogger,
        ids: TransactionIDGenerator,
        clock: Clock,
    ) -> None:
        self._repo = repo
        self._audit = audit
        self._ids = ids
        self._clock = clock

    def create(self, input_data: CreateInput) -> Transaction:
        if input_data.amount <= 0:
            raise ValueError("amount must be greater than zero")
        if input_data.type == "TRANSFER" and not input_data.goal_name.strip() and not input_data.jar_code.strip():
            raise ValueError("transfer must target a goal or jar")

        now = self._clock.now()
        transaction = Transaction(
            id=self._ids.new_transaction_id(),
            occurredAt=input_data.occurred_at or now,
            type=input_data.type,
            amount=input_data.amount,
            currency=input_data.currency.strip() or "VND",
            jarCode=input_data.jar_code.strip(),
            goalName=input_data.goal_name.strip(),
            accountName=input_data.account.strip(),
            isFixed=input_data.is_fixed,
            note=input_data.note.strip(),
            source=input_data.source.strip() or "manual",
            status=input_data.status or "confirmed",
            createdAt=now,
            updatedAt=now,
        )
        return self._repo.create_transaction(transaction)

    def list(self) -> list[Transaction]:
        return self._repo.list_transactions()

    def get(self, tx_id: str) -> Transaction:
        return self._repo.get_transaction(tx_id)

    def correct(self, tx_id: str, input_data: UpdateInput, reason: str, actor: str) -> Transaction:
        current = self._repo.get_transaction(tx_id)
        updated = self._apply_update(current, input_data)
        saved = self._repo.update_transaction(updated)
        self._log_audit("corrected", current, saved, reason, actor)
        return saved

    def undo(self, tx_id: str, reason: str, actor: str) -> Transaction:
        current = self._repo.get_transaction(tx_id)
        previous = current.model_copy(deep=True)
        current.status = "reverted"
        current.updated_at = self._clock.now()
        saved = self._repo.update_transaction(current)
        self._log_audit("undone", previous, saved, reason, actor)
        return saved

    def _apply_update(self, current: Transaction, input_data: UpdateInput) -> Transaction:
        if input_data.amount <= 0:
            raise ValueError("amount must be greater than zero")
        if input_data.type == "TRANSFER" and not input_data.goal_name.strip() and not input_data.jar_code.strip():
            raise ValueError("transfer must target a goal or jar")

        current.occurred_at = input_data.occurred_at
        current.type = input_data.type
        current.amount = input_data.amount
        current.currency = input_data.currency.strip()
        current.jar_code = input_data.jar_code.strip()
        current.goal_name = input_data.goal_name.strip()
        current.account = input_data.account.strip()
        current.is_fixed = input_data.is_fixed
        current.note = input_data.note.strip()
        if input_data.status:
            current.status = input_data.status
        current.updated_at = self._clock.now()
        return current

    def _log_audit(self, action: str, previous: Transaction, next_tx: Transaction, reason: str, actor: str) -> None:
        now = self._clock.now()
        self._audit.log(
            AuditEntry(
                id=f"AUD-{next_tx.id}-{int(now.timestamp() * 1_000_000_000)}",
                transactionId=next_tx.id,
                action=action,
                previousValue=json.dumps(previous.model_dump(mode="json", by_alias=True)),
                newValue=json.dumps(next_tx.model_dump(mode="json", by_alias=True)),
                reason=reason.strip(),
                actor=actor.strip(),
                createdAt=now,
            )
        )

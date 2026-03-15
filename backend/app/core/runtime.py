from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


class Clock:
    def now(self) -> datetime:
        return utc_now()


class TransactionIDGenerator:
    def new_transaction_id(self) -> str:
        return f"TX-{utc_now().strftime('%Y%m%d%H%M%S%f')}"

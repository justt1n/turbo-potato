from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from app.domain.assets.model import AssetItem, AssetOverview, JarTotal
from app.domain.sources.model import Source
from app.domain.transactions.model import Transaction


class TransactionsReader(Protocol):
    def list(self) -> list[Transaction]: ...


class SourcesReader(Protocol):
    def list(self) -> list[Source]: ...


class AssetsService:
    def __init__(self, transactions: TransactionsReader, sources: SourcesReader) -> None:
        self._transactions = transactions
        self._sources = sources

    def overview(self) -> AssetOverview:
        items: list[AssetItem] = []
        totals_by_jar: dict[str, dict[str, int]] = defaultdict(lambda: {"book": 0, "actual": 0, "count": 0})

        transactions = self._transactions.list()

        for source in self._sources.list():
            inflow_total = 0
            outflow_total = 0
            last_activity_at: str | None = None

            for tx in transactions:
                if tx.status == "reverted" or tx.account != source.code:
                    continue

                if tx.type in {"IN", "TRANSFER"}:
                    inflow_total += tx.amount
                elif tx.type == "OUT":
                    outflow_total += tx.amount

                occurred = tx.occurred_at.isoformat()
                if last_activity_at is None or occurred > last_activity_at:
                    last_activity_at = occurred

            book_balance = source.opening_balance + inflow_total - outflow_total
            actual_balance = source.actual_balance
            if source.kind == "gold":
                actual_balance = int(round(source.gold_quantity_chi * source.gold_price_per_chi))
            discrepancy = actual_balance - book_balance
            items.append(
                AssetItem(
                    code=source.code,
                    name=source.name,
                    kind=source.kind,
                    provider=source.provider,
                    linkedJarCode=source.linked_jar_code,
                    openingBalance=source.opening_balance,
                    inflowTotal=inflow_total,
                    outflowTotal=outflow_total,
                    bookBalance=book_balance,
                    actualBalance=actual_balance,
                    goldQuantityChi=source.gold_quantity_chi,
                    goldPricePerChi=source.gold_price_per_chi,
                    discrepancy=discrepancy,
                    isActive=source.is_active,
                    note=source.note,
                    lastActivityAt=last_activity_at,
                )
            )

            jar_code = source.linked_jar_code.strip()
            if jar_code:
                totals_by_jar[jar_code]["book"] += book_balance
                totals_by_jar[jar_code]["actual"] += actual_balance
                totals_by_jar[jar_code]["count"] += 1

        total_book = sum(item.book_balance for item in items)
        total_actual = sum(item.actual_balance for item in items)
        total_discrepancy = total_actual - total_book
        jar_totals = [
            JarTotal(
                jarCode=jar_code,
                totalBookBalance=values["book"],
                totalActualBalance=values["actual"],
                sourceCount=values["count"],
            )
            for jar_code, values in sorted(totals_by_jar.items())
        ]

        return AssetOverview(
            totalBookBalance=total_book,
            totalActualBalance=total_actual,
            totalDiscrepancy=total_discrepancy,
            activeSources=sum(1 for item in items if item.is_active),
            jarTotals=jar_totals,
            items=items,
        )

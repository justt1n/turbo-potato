from __future__ import annotations

from app.infrastructure.sheets.repositories import GoogleJarsRepository, GoogleSourcesRepository


class FakeValuesClient:
    def __init__(self, rows: dict[str, list[list[object]]] | None = None) -> None:
        self.rows = rows or {}

    def append(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None:
        raise AssertionError("append should not be used in repository read tests")

    def get(self, spreadsheet_id: str, read_range: str) -> list[list[object]]:
        return self.rows.get(read_range, [])

    def update(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None:
        raise AssertionError("update should not be used in repository read tests")


def test_list_jars_handles_legacy_rows_without_note_column() -> None:
    client = FakeValuesClient(
        rows={
            "Jars!A2:G": [
                ["LegacyJar", "Hũ cũ", "cash", "1000000", "1200000", "true"],
            ]
        }
    )

    repo = GoogleJarsRepository(client, "sheet-id")
    items = repo.list_jars()

    assert len(items) == 1
    assert items[0].code == "LegacyJar"
    assert items[0].actual_balance == 1200000
    assert items[0].note == ""


def test_list_sources_handles_rows_missing_new_columns() -> None:
    client = FakeValuesClient(
        rows={
            "Sources!A2:K": [
                ["Wallet_1", "Ví chính", "wallet", "", "", "500000", "450000"],
            ]
        }
    )

    repo = GoogleSourcesRepository(client, "sheet-id")
    items = repo.list_sources()

    assert len(items) == 1
    assert items[0].code == "Wallet_1"
    assert items[0].actual_balance == 450000
    assert items[0].gold_quantity_chi == 0
    assert items[0].note == ""

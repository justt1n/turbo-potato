from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ValuesAPI(Protocol):
    def append(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None: ...

    def get(self, spreadsheet_id: str, read_range: str) -> list[list[object]]: ...

    def update(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None: ...


class SpreadsheetAdminAPI(Protocol):
    def get_sheet_titles(self, spreadsheet_id: str) -> list[str]: ...

    def add_sheets(self, spreadsheet_id: str, titles: list[str]) -> None: ...


class Bootstrapper(Protocol):
    def bootstrap(self) -> None: ...


@dataclass(slots=True)
class SheetSpec:
    title: str
    headers: list[object]
